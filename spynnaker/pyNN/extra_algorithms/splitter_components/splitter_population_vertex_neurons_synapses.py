# Copyright (c) 2020 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from collections import defaultdict
import logging
import math
from typing import Dict, List, Optional, Sequence, Set, Tuple, cast

from numpy import floating
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ordered_set import OrderedSet

from pacman.model.resources import AbstractSDRAM, MultiRegionSDRAM
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.model.graphs import AbstractEdgePartition, AbstractVertex
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import (
    MachineEdge, SourceSegmentedSDRAMMachinePartition, SDRAMMachineEdge,
    MulticastEdgePartition, MachineVertex)
from pacman.model.graphs.common import Slice
from pacman.utilities.utility_objs import ChipCounter

from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.models.projection import Projection
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.neuron import (
    PopulationNeuronsMachineVertex, PopulationSynapsesMachineVertexLead,
    PopulationSynapsesMachineVertexShared, NeuronProvenance, SynapseProvenance,
    SpikeProcessingFastProvenance)
from spynnaker.pyNN.models.neuron.population_neurons_machine_vertex import (
    SDRAM_PARAMS_SIZE as NEURONS_SDRAM_PARAMS_SIZE, NeuronMainProvenance)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
from spynnaker.pyNN.models.neuron.neuron_data import NeuronData
from spynnaker.pyNN.models.abstract_models import SendsSynapticInputsOverSDRAM
from spynnaker.pyNN.models.neuron.population_synapses_machine_vertex_common \
    import (
        SDRAM_PARAMS_SIZE as SYNAPSES_SDRAM_PARAMS_SIZE, KEY_CONFIG_SIZE,
        PopulationSynapsesMachineVertexCommon)
from spynnaker.pyNN.models.neuron.synaptic_matrices import (
    SynapseRegionReferences)
from spynnaker.pyNN.utilities.constants import (
    SYNAPSE_SDRAM_PARTITION_ID, SPIKE_PARTITION_ID, MAX_RING_BUFFER_BITS)
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_sdram_for_bit_field_region)
from spynnaker.pyNN.models.spike_source.spike_source_poisson_machine_vertex \
    import (
        SpikeSourcePoissonMachineVertex)

from .splitter_population_vertex import SplitterPopulationVertex
from .abstract_supports_one_to_one_sdram_input import (
    AbstractSupportsOneToOneSDRAMInput)

logger = FormatAdapter(logging.getLogger(__name__))


class SplitterPopulationVertexNeuronsSynapses(
        SplitterPopulationVertex, AbstractSupportsOneToOneSDRAMInput):
    """
    Splits an :py:class:`PopulationVertex` so that there are separate
    neuron cores each being fed by one or more synapse cores.  Incoming
    one-to-one Poisson cores are also added here if they meet the criteria.
    """

    __slots__ = (
        # All the neuron cores
        "__neuron_vertices",
        # All the synapse cores
        "__synapse_vertices",
        # Any application Poisson sources that are handled here
        "__poisson_sources",
        # The next synapse core to use for an incoming machine edge
        "__next_synapse_index",
        # The incoming vertices cached
        "__incoming_vertices",
        # The internal multicast partitions
        "__multicast_partitions",
        # The internal SDRAM partitions
        "__sdram_partitions",
        # The same chip groups
        "__same_chip_groups",
        # The application vertex sources that are neuromodulators
        "__neuromodulators")

    def __init__(self) -> None:
        super().__init__()

        self.__next_synapse_index = 0
        self.__neuron_vertices: List[PopulationNeuronsMachineVertex] = []
        self.__synapse_vertices: List[
            PopulationSynapsesMachineVertexCommon] = []
        self.__multicast_partitions: List[MulticastEdgePartition] = []
        self.__sdram_partitions: List[
            SourceSegmentedSDRAMMachinePartition] = []
        self.__same_chip_groups: List[Tuple[
            List[MachineVertex], AbstractSDRAM]] = []
        self.__neuromodulators: Set[ApplicationVertex] = set()
        self.__incoming_vertices: List[List[MachineVertex]] = []
        self.__poisson_sources: Set[SpikeSourcePoissonVertex] = set()

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter: ChipCounter) -> None:
        label = self.governed_app_vertex.label or ""

        # Structural plasticity can only be run on a single synapse core
        if (isinstance(self.governed_app_vertex.synapse_dynamics,
                       AbstractSynapseDynamicsStructural) and
                self.governed_app_vertex.n_synapse_cores_required != 1):
            raise SynapticConfigurationException(
                "The current implementation of structural plasticity can only"
                " be run on a single synapse core.  Please ensure the number"
                " of synapse cores is set to 1")

        # Do some checks to make sure everything is likely to fit
        n_atom_bits = self.governed_app_vertex.get_n_atom_bits()
        n_synapse_types = \
            self.governed_app_vertex.neuron_impl.get_n_synapse_types()
        if (n_atom_bits + get_n_bits(n_synapse_types) +
                get_n_bits(self.max_support_delay())) > MAX_RING_BUFFER_BITS:
            raise SynapticConfigurationException(
                "The combination of the number of neurons per core "
                f"({n_atom_bits}), the number of synapse types "
                f"({n_synapse_types}), and the maximum delay per core "
                f"({self.max_support_delay()}) will require too much DTCM. "
                "Please reduce one or more of these values.")

        incoming_direct_poisson = self.__handle_poisson_sources(label)

        atoms_per_core = min(
            self.governed_app_vertex.get_max_atoms_per_core(),
            self.governed_app_vertex.n_atoms)

        # Work out the ring buffer shifts based on all incoming things
        rb_shifts = self.governed_app_vertex.get_ring_buffer_shifts()
        weight_scales = self.governed_app_vertex.get_weight_scales(rb_shifts)

        # We add the SDRAM edge SDRAM to the neuron resources so it is
        # accounted for within the placement
        n_synapse_cores = self.governed_app_vertex.n_synapse_cores_required
        n_incoming = n_synapse_cores + len(self.__poisson_sources)
        edge_sdram = PopulationNeuronsMachineVertex.get_n_bytes_for_transfer(
            atoms_per_core, n_synapse_types)
        sdram_edge_sdram = edge_sdram * n_incoming

        # Get maximum resources for neurons for each split
        neuron_sdram = self.__get_neuron_sdram(
            atoms_per_core, sdram_edge_sdram)

        # Get resources for synapses
        structural_sz = max(
            self.governed_app_vertex.get_structural_dynamics_size(
                atoms_per_core), BYTES_PER_WORD)
        all_syn_block_sz = max(
            self.governed_app_vertex.get_synapses_size(atoms_per_core),
            BYTES_PER_WORD)
        shared_synapse_sdram = self.__get_shared_synapse_sdram(
            atoms_per_core, all_syn_block_sz, structural_sz)
        lead_synapse_core_sdram = self.__get_synapse_sdram(
            atoms_per_core, shared_synapse_sdram)
        shared_synapse_core_sdram = self.__get_synapse_sdram(atoms_per_core)
        synapse_regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        synaptic_matrices = SynapticMatrices(
            self.governed_app_vertex, synapse_regions, atoms_per_core,
            weight_scales, all_syn_block_sz)
        neuron_data = NeuronData(self.governed_app_vertex)

        for index in range(n_synapse_cores):
            self.__incoming_vertices.append([])

        for index, vertex_slice in enumerate(self._get_fixed_slices()):
            # Create the neuron vertex for the slice
            neuron_vertex = self.__add_neuron_core(
                vertex_slice, neuron_sdram, label, index, rb_shifts,
                weight_scales, neuron_data, atoms_per_core)
            sdram: AbstractSDRAM = neuron_sdram
            source_vertices: List[MachineVertex] = list()
            source_sdram_vertices: List[SendsSynapticInputsOverSDRAM] = list()

            # Add the first vertex
            synapse_references, syn_label, feedback_partition, lead_vtx = \
                self.__add_lead_synapse_core(
                    vertex_slice, structural_sz, lead_synapse_core_sdram,
                    label, rb_shifts, weight_scales, neuron_vertex,
                    atoms_per_core, synaptic_matrices)
            sdram += lead_synapse_core_sdram
            source_vertices.append(lead_vtx)
            source_sdram_vertices.append(lead_vtx)

            # Do the remaining synapse cores
            for i in range(1, n_synapse_cores):
                shared_vtx = self.__add_shared_synapse_core(
                    syn_label, i, vertex_slice, synapse_references,
                    shared_synapse_core_sdram, feedback_partition,
                    neuron_vertex)
                sdram += shared_synapse_core_sdram
                source_vertices.append(shared_vtx)
                source_sdram_vertices.append(shared_vtx)

            # Add resources for Poisson vertices
            poisson_vertices = incoming_direct_poisson[vertex_slice]
            for poisson_vertex, _possion_edge in poisson_vertices:
                source_vertices.append(poisson_vertex)
                source_sdram_vertices.append(poisson_vertex)
                sdram += poisson_vertex.sdram_required

            # Add the cores
            n_cores = n_incoming + 1
            chip_counter.add_core(sdram, n_cores=n_cores)

            # Create an SDRAM edge partition
            sdram_partition = SourceSegmentedSDRAMMachinePartition(
                SYNAPSE_SDRAM_PARTITION_ID, source_vertices)
            self.__sdram_partitions.append(sdram_partition)
            neuron_vertex.set_sdram_partition(sdram_partition)

            # Add SDRAM edges for synapse vertices
            for source_vertex in source_vertices:
                sdram_partition.add_edge(SDRAMMachineEdge(
                    source_vertex, neuron_vertex,
                    f"SDRAM {source_vertex.label}-->{neuron_vertex.label}"))
            for source_vertex_over_sdram in source_sdram_vertices:
                source_vertex_over_sdram.set_sdram_partition(sdram_partition)

            self.__same_chip_groups.append(
                ([*source_vertices, neuron_vertex], sdram))

        # Find incoming neuromodulators
        for proj in self.governed_app_vertex.incoming_projections:
            # pylint: disable=protected-access
            edge = proj._projection_edge
            if edge.is_neuromodulation:
                self.__neuromodulators.add(edge.pre_vertex)

    def __add_neuron_core(
            self, vertex_slice: Slice, sdram: AbstractSDRAM,
            label: str, index: int, rb_shifts: List[int],
            weight_scales: NDArray[floating], neuron_data: NeuronData,
            atoms_per_core: int) -> PopulationNeuronsMachineVertex:
        """
        Add a neuron core for for a slice of neurons.

        :param vertex_slice:
            The slice of neurons to put on the core
        :param sdram:
        :param label: The name to give the core
        :param index: The index of the slice in the ordered list of slices
        :param rb_shifts:
            The computed ring-buffer shift values to use to get the weights
            back to S1615 values
        :param weight_scales:
            The scale to apply to weights to encode them in the 16-bit synapses
        :return: The neuron vertex created and the resources used
        """
        neuron_vertex = PopulationNeuronsMachineVertex(
            sdram,
            f"{label}_Neurons:{vertex_slice.lo_atom}",
            self.governed_app_vertex, vertex_slice, index, rb_shifts,
            weight_scales, neuron_data, atoms_per_core)
        self.governed_app_vertex.remember_machine_vertex(neuron_vertex)
        self.__neuron_vertices.append(neuron_vertex)

        return neuron_vertex

    def __add_lead_synapse_core(
            self, vertex_slice: Slice, structural_sz: int,
            lead_synapse_core_sdram: AbstractSDRAM, label: str,
            rb_shifts: List[int], weight_scales: NDArray[floating],
            neuron_vertex: PopulationNeuronsMachineVertex,
            atoms_per_core: int, synaptic_matrices: SynapticMatrices) -> Tuple[
                SynapseRegionReferences, str,
                Optional[MulticastEdgePartition],
                PopulationSynapsesMachineVertexLead]:
        """
        Add the first synapse core for a neuron core.  This core will
        generate all the synaptic data required.

        :param vertex_slice:
            The slice of neurons on the neuron core
        :param lead_synapse_core_sdram:
            The SDRAM that will be used by every lead synapse core
        :param label: The name to give the core
        :param rb_shifts:
            The computed ring-buffer shift values to use to get the weights
            back to S1615 values
        :param weight_scales:
            The scale to apply to weights to encode them in the 16-bit synapses
        :param neuron_vertex:
            The neuron vertex the synapses will feed into
        :param atoms_per_core: The maximum atoms per core
        :return: References to the synapse regions that can be used by a shared
            synapse core, the basic label for the synapse cores,
            the feedback partition (if needed), and the lead synapse core
        """
        synapse_references = SynapseRegionReferences(
            *SpynnakerDataView.get_next_ds_references(7))
        syn_label = (
            f"{label}_Synapses:{vertex_slice.lo_atom}")

        # Do the lead synapse core
        lead_synapse_vertex = PopulationSynapsesMachineVertexLead(
            lead_synapse_core_sdram, f"{syn_label}(0)",
            self.governed_app_vertex, vertex_slice, rb_shifts, weight_scales,
            structural_sz, synapse_references, atoms_per_core,
            synaptic_matrices)
        self.governed_app_vertex.remember_machine_vertex(lead_synapse_vertex)
        self.__synapse_vertices.append(lead_synapse_vertex)
        self.__incoming_vertices[0].append(lead_synapse_vertex)

        part = self.__add_plastic_feedback(neuron_vertex, lead_synapse_vertex)

        return synapse_references, syn_label, part, lead_synapse_vertex

    def __add_shared_synapse_core(
            self, syn_label: str, s_index: int, vertex_slice: Slice,
            synapse_references: SynapseRegionReferences,
            shared_synapse_sdram: AbstractSDRAM,
            feedback_partition: Optional[AbstractEdgePartition],
            neuron_vertex: PopulationNeuronsMachineVertex)\
            -> PopulationSynapsesMachineVertexShared:
        """
        Add a second or subsequent synapse core.  This will reference the
        synaptic data generated by the lead synapse core.

        :param syn_label: The basic synapse core label to be extended
        :param s_index: The index of the synapse core (0 is the lead core)
        :param vertex_slice: The slice of neurons on the neuron core
        :param synapse_references: References to the synapse regions
        :param shared_synapse_sdram:
        :param feedback_partition:
`       :param neuron_vertex:
            The neuron vertex the synapses will feed into
        :return: The
        """
        synapse_label = f"{syn_label}({s_index})"
        synapse_vertex = PopulationSynapsesMachineVertexShared(
            shared_synapse_sdram, synapse_label, self.governed_app_vertex,
            vertex_slice, synapse_references)
        self.governed_app_vertex.remember_machine_vertex(synapse_vertex)
        self.__synapse_vertices.append(synapse_vertex)
        self.__incoming_vertices[s_index].append(synapse_vertex)

        if feedback_partition is not None:
            neuron_to_synapse_edge = MachineEdge(neuron_vertex, synapse_vertex)
            feedback_partition.add_edge(neuron_to_synapse_edge)
            synapse_vertex.set_neuron_vertex_and_partition_id(
                neuron_vertex, SPIKE_PARTITION_ID)

        return synapse_vertex

    def __add_plastic_feedback(
            self, neuron_vertex: PopulationNeuronsMachineVertex,
            synapse_vertex: PopulationSynapsesMachineVertexCommon) -> Optional[
                MulticastEdgePartition]:
        """
        Add an edge if needed from the neuron core back to the synapse core
        to allow the synapse core to process plastic synapses.

        :param neuron_vertex: The neuron vertex to start the edge at
        :param synapse_vertex: A synapse vertex to feed the spikes back to
        """
        # If synapse dynamics is not simply static, link the neuron vertex
        # back to the synapse vertex
        if self.governed_app_vertex.synapse_dynamics is not None and \
                not isinstance(self.governed_app_vertex.synapse_dynamics,
                               SynapseDynamicsStatic):
            if self.governed_app_vertex.self_projection is None:
                feedback_partition = MulticastEdgePartition(
                    neuron_vertex, SPIKE_PARTITION_ID)
                neuron_to_synapse_edge = MachineEdge(
                    neuron_vertex, synapse_vertex)
                feedback_partition.add_edge(neuron_to_synapse_edge)
                self.__multicast_partitions.append(feedback_partition)
                synapse_vertex.set_neuron_vertex_and_partition_id(
                    neuron_vertex, SPIKE_PARTITION_ID)
                return feedback_partition
            synapse_vertex.set_neuron_vertex_and_partition_id(
                neuron_vertex, SPIKE_PARTITION_ID)
        return None

    @property
    def __too_many_cores(self) -> bool:
        version = SpynnakerDataView.get_machine_version()
        incoming = self.governed_app_vertex.incoming_poisson_projections
        n_synapse_cores = self.governed_app_vertex.n_synapse_cores_required
        return ((len(incoming) + n_synapse_cores + 1) >=
                (version.max_cores_per_chip - version.n_scamp_cores))

    def __handle_poisson_sources(self, label: str) -> Dict[Slice, List[Tuple[
            SpikeSourcePoissonMachineVertex, ProjectionApplicationEdge]]]:
        """
        Go through the incoming projections and find Poisson sources with
        splitters that work with us, and one-to-one connections that will
        then work with SDRAM.

        :param label: Base label to give to the Poisson cores
        """
        # The only way to avoid circular imports is to import here
        # pylint: disable=import-outside-toplevel
        from spynnaker.pyNN.extra_algorithms.splitter_components\
            .splitter_utils import is_direct_poisson_source
        incoming_direct_poisson: Dict[Slice, List[Tuple[
            SpikeSourcePoissonMachineVertex,
            ProjectionApplicationEdge]]] = defaultdict(list)
        # If there are going to be too many to fit on a chip, don't do direct
        # Poisson
        if self.__too_many_cores:
            return incoming_direct_poisson
        for proj in self.governed_app_vertex.incoming_poisson_projections:
            # pylint: disable=protected-access
            edge = proj._projection_edge
            pre_vertex = cast(SpikeSourcePoissonVertex, edge.pre_vertex)
            conn = proj._synapse_information.connector
            dynamics = proj._synapse_information.synapse_dynamics
            delay = proj._synapse_information.delays
            if is_direct_poisson_source(self.governed_app_vertex, pre_vertex,
                                        conn, dynamics, delay):
                # Create the direct Poisson vertices here; the splitter
                # for the Poisson will create any others as needed
                for vertex_slice in self._get_fixed_slices():
                    sdram = pre_vertex.get_sdram_used_by_atoms(vertex_slice)
                    poisson_m_vertex = pre_vertex.create_machine_vertex(
                        vertex_slice, sdram, label=(
                            f"{label}_Poisson:"
                            f"{vertex_slice.lo_atom}"))
                    pre_vertex.remember_machine_vertex(poisson_m_vertex)
                    incoming_direct_poisson[vertex_slice].append(
                        (poisson_m_vertex, edge))

                # Keep track of sources that have been handled
                self.__poisson_sources.add(pre_vertex)
        return incoming_direct_poisson

    @overrides(AbstractSupportsOneToOneSDRAMInput.handles_source_vertex)
    def handles_source_vertex(self, projection: Projection) -> bool:
        # If there are too many incoming Poisson sources, we can't do this
        if self.__too_many_cores:
            return False

        # The only way to avoid circular imports is to import here
        # pylint: disable=import-outside-toplevel
        from spynnaker.pyNN.extra_algorithms.splitter_components\
            .splitter_utils import is_direct_poisson_source

        # pylint: disable=protected-access
        edge = projection._projection_edge
        pre_vertex = edge.pre_vertex
        connector = projection._synapse_information.connector
        dynamics = projection._synapse_information.synapse_dynamics
        delay = projection._synapse_information.delays
        return is_direct_poisson_source(
            self.governed_app_vertex, pre_vertex, connector, dynamics, delay)

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self) -> Sequence[Slice]:
        return self._get_fixed_slices()

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self) -> Sequence[Slice]:
        return self._get_fixed_slices()

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id: str) -> Sequence[
            PopulationNeuronsMachineVertex]:
        return self.__neuron_vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id: str) -> Sequence[
            PopulationSynapsesMachineVertexCommon]:
        return self.__synapse_vertices

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex: ApplicationVertex,
            partition_id: str) -> Sequence[
                Tuple[MachineVertex, Sequence[AbstractVertex]]]:
        # If delayed get the real pre-vertex
        if isinstance(source_vertex, DelayExtensionVertex):
            pre_vertex = cast(
                PopulationApplicationVertex, source_vertex.source_vertex)
        elif isinstance(source_vertex, PopulationApplicationVertex):
            pre_vertex = source_vertex
        else:
            raise ValueError(
                f"unsupported source vertex type: {type(source_vertex)}")

        # Filter out edges from Poisson sources being done using SDRAM
        if pre_vertex in self.__poisson_sources:
            return []

        # If the incoming edge targets the reward or punishment receptors
        # then it needs to be treated differently
        if pre_vertex in self.__neuromodulators:
            # In this instance, choose to send to all synapse vertices
            return [(v, [source_vertex])
                    for s in self.__incoming_vertices for v in s]

        # Get the set of connected sources overall using the real pre-vertex
        targets: Dict[MachineVertex, OrderedSet[AbstractVertex]] = defaultdict(
            OrderedSet)
        for proj in self.governed_app_vertex.get_incoming_projections_from(
                pre_vertex):
            # pylint: disable=protected-access
            s_info = proj._synapse_information
            # Use the original source vertex here to ensure the actual machine
            # vertices of the source vertex make it in
            for (tgt, srcs) in s_info.synapse_dynamics.get_connected_vertices(
                    s_info, source_vertex, self.governed_app_vertex):
                targets[tgt].update(srcs)

        # Split the incoming machine vertices so that they are in ~power of 2
        # groups, using the original source vertex to get the right machine
        # vertices
        sources = source_vertex.splitter.get_out_going_vertices(partition_id)
        n_sources = len(sources)
        n_synapse_cores = self.governed_app_vertex.n_synapse_cores_required
        sources_per_vertex = max(1, int(2 ** math.ceil(math.log2(
            n_sources / n_synapse_cores))))

        # Start on a different index each time to "even things out"
        index = self.__next_synapse_index
        self.__next_synapse_index = (
            (self.__next_synapse_index + 1) % n_synapse_cores)
        result: List[Tuple[MachineVertex, List[MachineVertex]]] = list()
        for start in range(0, n_sources, sources_per_vertex):
            end = min(start + sources_per_vertex, n_sources)
            source_range = sources[start:end]
            for s_vertex in self.__incoming_vertices[index]:
                targets_filtered = targets[s_vertex]
                filtered = [s for s in source_range
                            if (s in targets_filtered or
                                s.app_vertex in targets_filtered)]
                result.append((s_vertex, filtered))
            index = (index + 1) % n_synapse_cores

        return result

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(
            self, variable_to_record: str) -> Sequence[MachineVertex]:
        if self.governed_app_vertex.neuron_recorder.is_recordable(
                variable_to_record):
            return self.__neuron_vertices
        return self.__synapse_vertices

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self) -> None:
        self.__neuron_vertices = []
        self.__synapse_vertices = []
        self.__multicast_partitions = []
        self.__sdram_partitions = []
        self.__same_chip_groups = []
        self.__poisson_sources = set()
        self.__incoming_vertices = []

    def __get_neuron_sdram(
            self, n_atoms: int, sdram_edge_sdram: int) -> MultiRegionSDRAM:
        """
        Gets the resources of the neurons of a slice of atoms from a given
        application vertex.
        """
        n_record = len(self.governed_app_vertex.neuron_recordables)
        variable_sdram = \
            self.governed_app_vertex.get_max_neuron_variable_sdram(n_atoms)
        sdram = MultiRegionSDRAM()
        sdram.merge(self.governed_app_vertex.get_common_constant_sdram(
            n_record, NeuronProvenance.N_ITEMS + NeuronMainProvenance.N_ITEMS,
            PopulationNeuronsMachineVertex.COMMON_REGIONS))
        sdram.merge(self.governed_app_vertex.get_neuron_constant_sdram(
            n_atoms, PopulationNeuronsMachineVertex.NEURON_REGIONS))
        sdram.add_cost(
            PopulationNeuronsMachineVertex.REGIONS.SDRAM_EDGE_PARAMS,
            NEURONS_SDRAM_PARAMS_SIZE)
        sdram.nest(
            len(PopulationNeuronsMachineVertex.REGIONS), variable_sdram)
        sdram.add_cost(
            len(PopulationNeuronsMachineVertex.REGIONS) + 1, sdram_edge_sdram)

        # return the total resources.
        return sdram

    def __shared_synapse_sdram(
            self, independent_synapse_sdram: MultiRegionSDRAM,
            proj_dependent_sdram: MultiRegionSDRAM, all_syn_block_sz: int,
            structural_sz: int, dynamics_sz: int) -> MultiRegionSDRAM:
        """
        Get the SDRAM shared between synapse cores.
        """
        regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.merge(independent_synapse_sdram)
        sdram.merge(proj_dependent_sdram)
        sdram.add_cost(regions.synaptic_matrix, all_syn_block_sz)
        sdram.add_cost(regions.structural_dynamics, structural_sz)
        sdram.add_cost(regions.synapse_dynamics, dynamics_sz)
        return sdram

    def __get_shared_synapse_sdram(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int) -> MultiRegionSDRAM:
        independent_synapse_sdram = self.__independent_synapse_sdram()
        proj_dependent_sdram = self.__proj_dependent_synapse_sdram()
        dynamics_sz = self.governed_app_vertex.get_synapse_dynamics_size(
            n_atoms)
        dynamics_sz = max(dynamics_sz, BYTES_PER_WORD)
        return self.__shared_synapse_sdram(
            independent_synapse_sdram, proj_dependent_sdram,
            all_syn_block_sz, structural_sz, dynamics_sz)

    def __get_synapse_sdram(
            self, n_atoms: int,
            shared_sdram: Optional[MultiRegionSDRAM] = None
            ) -> MultiRegionSDRAM:
        """
        Get the resources of the synapses of a slice of atoms from a
        given application vertex.

        :param shared_sdram:
            The SDRAM shared between cores, if this is to be included
        """
        n_record = len(self.governed_app_vertex.synapse_recordables)
        variable_sdram = \
            self.governed_app_vertex.get_max_synapse_variable_sdram(n_atoms)
        sdram = MultiRegionSDRAM()
        sdram.merge(self.governed_app_vertex.get_common_constant_sdram(
            n_record,
            SynapseProvenance.N_ITEMS + SpikeProcessingFastProvenance.N_ITEMS,
            PopulationSynapsesMachineVertexLead.COMMON_REGIONS))

        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.REGIONS.SDRAM_EDGE_PARAMS,
            SYNAPSES_SDRAM_PARAMS_SIZE)
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.REGIONS.KEY_REGION,
            KEY_CONFIG_SIZE)
        sdram.nest(
            len(PopulationSynapsesMachineVertexLead.REGIONS) + 1,
            variable_sdram)
        if shared_sdram is not None:
            sdram.merge(shared_sdram)

        # return the total resources.
        return sdram

    def __independent_synapse_sdram(self) -> MultiRegionSDRAM:
        """
        Get the SDRAM used by all synapse cores independent of projections.
        """
        regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            regions.synapse_params,
            max(self.governed_app_vertex.get_synapse_params_size(),
                BYTES_PER_WORD))
        return sdram

    def __proj_dependent_synapse_sdram(self) -> MultiRegionSDRAM:
        """
        Get the SDRAM used by synapse cores dependent on the projections.
        """
        regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            regions.pop_table,
            max(MasterPopTableAsBinarySearch.get_master_population_table_size(
                self.governed_app_vertex.incoming_projections),
                BYTES_PER_WORD))
        sdram.add_cost(
            regions.connection_builder,
            max(self.governed_app_vertex.get_synapse_expander_size(),
                BYTES_PER_WORD))
        sdram.add_cost(
            regions.bitfield_filter,
            max(get_sdram_for_bit_field_region(
                self.governed_app_vertex.incoming_projections),
                BYTES_PER_WORD))
        return sdram

    @overrides(AbstractSplitterCommon.get_same_chip_groups)
    def get_same_chip_groups(self) -> List[
            Tuple[List[MachineVertex], AbstractSDRAM]]:
        return self.__same_chip_groups

    @overrides(AbstractSplitterCommon.get_internal_multicast_partitions)
    def get_internal_multicast_partitions(
            self) -> List[MulticastEdgePartition]:
        return self.__multicast_partitions

    @overrides(AbstractSplitterCommon.get_internal_sdram_partitions)
    def get_internal_sdram_partitions(
            self) -> List[SourceSegmentedSDRAMMachinePartition]:
        return self.__sdram_partitions

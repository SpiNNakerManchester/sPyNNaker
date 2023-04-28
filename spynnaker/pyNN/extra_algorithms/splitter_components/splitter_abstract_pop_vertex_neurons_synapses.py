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
import math
import logging
from collections import defaultdict
from spinn_utilities.overrides import overrides
from spinn_utilities.log import FormatAdapter
from spinn_utilities.ordered_set import OrderedSet
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import MultiRegionSDRAM
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from pacman.model.graphs.machine import (
    MachineEdge, SourceSegmentedSDRAMMachinePartition, SDRAMMachineEdge,
    MulticastEdgePartition)
from pacman.utilities.algorithm_utilities.partition_algorithm_utilities \
    import get_multidimensional_slices
from data_specification.reference_context import ReferenceContext
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.neuron import (
    PopulationNeuronsMachineVertex, PopulationSynapsesMachineVertexLead,
    PopulationSynapsesMachineVertexShared, NeuronProvenance, SynapseProvenance,
    AbstractPopulationVertex, SpikeProcessingFastProvenance)
from spynnaker.pyNN.models.neuron.population_neurons_machine_vertex import (
    SDRAM_PARAMS_SIZE as NEURONS_SDRAM_PARAMS_SIZE, NeuronMainProvenance)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
from spynnaker.pyNN.models.neuron.neuron_data import NeuronData
from spynnaker.pyNN.models.neuron.population_synapses_machine_vertex_common \
    import (SDRAM_PARAMS_SIZE as SYNAPSES_SDRAM_PARAMS_SIZE, KEY_CONFIG_SIZE,
            SynapseRegions)
from spynnaker.pyNN.utilities.constants import (
    SYNAPSE_SDRAM_PARTITION_ID, SPIKE_PARTITION_ID)
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_sdram_for_bit_field_region)

from .splitter_poisson_delegate import SplitterPoissonDelegate
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from .abstract_supports_one_to_one_sdram_input import (
    AbstractSupportsOneToOneSDRAMInput)

logger = FormatAdapter(logging.getLogger(__name__))

# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14

# The maximum number of cores to consider acceptable for a single chip
_MAX_CORES = 15


class SplitterAbstractPopulationVertexNeuronsSynapses(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay,
        AbstractSupportsOneToOneSDRAMInput):
    """
    Splits an :py:class:`AbstractPopulationVertex` so that there are separate
    neuron cores each being fed by one or more synapse cores.  Incoming
    one-to-one Poisson cores are also added here if they meet the criteria.
    """

    __slots__ = [
        # All the neuron cores
        "__neuron_vertices",
        # All the synapse cores
        "__synapse_vertices",
        # The synapse cores split by neuron core
        "__synapse_verts_by_neuron",
        # The number of synapse cores per neuron core
        "__n_synapse_vertices",
        # Any application Poisson sources that are handled here
        "__poisson_sources",
        # The maximum delay supported
        "__max_delay",
        # The user-set maximum delay, for reset
        "__user_max_delay",
        # Whether you expect delay extensions to be asked to be created
        "__expect_delay_extension",
        # The user-set allowing of delay extensions
        "__user_allow_delay_extension",
        # The fixed slices the vertices are divided into
        "__slices",
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
        "__neuromodulators"
        ]

    def __init__(self, n_synapse_vertices=1,
                 max_delay=None,
                 allow_delay_extension=None):
        """
        :param int n_synapse_vertices:
            The number of synapse cores per neuron core
        :param max_delay:
            The maximum delay supported by each synapse core; by default this
            is computed based on the number of atoms per core, the number of
            synapse types, and the space available for delays on the core
        :type max_delay: int or None
        :param allow_delay_extension:
            Whether delay extensions are allowed in the network. If max_delay
            is provided, this will default to True.  If max_delay is not
            provided, and this is given as `None`, it will be computed based on
            whether delay extensions should be needed.
        :type allow_delay_extension: bool or None
        """
        super(SplitterAbstractPopulationVertexNeuronsSynapses, self).__init__()
        AbstractSpynnakerSplitterDelay.__init__(self)

        if n_synapse_vertices + 1 > _MAX_CORES:
            raise SynapticConfigurationException(
                f"At most, there can be {_MAX_CORES - 1} synaptic vertices")

        self.__n_synapse_vertices = n_synapse_vertices
        self.__max_delay = max_delay
        self.__user_max_delay = max_delay
        self.__user_allow_delay_extension = allow_delay_extension
        if max_delay is None:
            # to be calcutaed by __update_max_delay
            self.__expect_delay_extension = None
        else:
            # The user may ask for the delay even if then told no
            self.__expect_delay_extension = True
            if allow_delay_extension is None:
                self.__user_allow_delay_extension = True
        self.__slices = None
        self.__next_synapse_index = 0
        # redefined by create_machine_vertices before first use so style
        self.__neuron_vertices = None
        self.__synapse_vertices = None
        self.__synapse_verts_by_neuron = None
        self.__multicast_partitions = []
        self.__sdram_partitions = []
        self.__same_chip_groups = []
        self.__neuromodulators = set()
        self.__incoming_vertices = []
        self.__poisson_sources = []

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                f"The vertex {app_vertex} cannot be supported by the "
                "SplitterAbstractPopVertexNeuronsSynapses as the only vertex "
                "supported by this splitter is a AbstractPopulationVertex. "
                "Please use the correct splitter for your vertex and try "
                "again.")

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self.governed_app_vertex
        label = app_vertex.label

        # Structural plasticity can only be run on a single synapse core
        if (isinstance(app_vertex.synapse_dynamics,
                       AbstractSynapseDynamicsStructural) and
                self.__n_synapse_vertices != 1):
            raise SynapticConfigurationException(
                "The current implementation of structural plasticity can only"
                " be run on a single synapse core.  Please ensure the number"
                " of synapse cores is set to 1")

        # Do some checks to make sure everything is likely to fit
        n_atom_bits = app_vertex.get_n_atom_bits()
        n_synapse_types = app_vertex.neuron_impl.get_n_synapse_types()
        if (n_atom_bits + get_n_bits(n_synapse_types) +
                get_n_bits(self.max_support_delay())) > MAX_RING_BUFFER_BITS:
            raise SynapticConfigurationException(
                "The combination of the number of neurons per core "
                f"({n_atom_bits}), the number of synapse types "
                f"({n_synapse_types}), and the maximum delay per core "
                f"({self.max_support_delay()}) will require too much DTCM. "
                "Please reduce one or more of these values.")

        self.__neuron_vertices = list()
        self.__synapse_vertices = list()
        self.__synapse_verts_by_neuron = defaultdict(list)

        incoming_direct_poisson = self.__handle_poisson_sources(label)

        atoms_per_core = min(
            app_vertex.get_max_atoms_per_core(), app_vertex.n_atoms)

        # Work out the ring buffer shifts based on all incoming things
        rb_shifts = app_vertex.get_ring_buffer_shifts()
        weight_scales = app_vertex.get_weight_scales(rb_shifts)

        # We add the SDRAM edge SDRAM to the neuron resources so it is
        # accounted for within the placement
        n_incoming = self.__n_synapse_vertices + len(self.__poisson_sources)
        edge_sdram = PopulationNeuronsMachineVertex.get_n_bytes_for_transfer(
            atoms_per_core, n_synapse_types)
        sdram_edge_sdram = edge_sdram * n_incoming

        # Get maximum resources for neurons for each split
        neuron_sdram = self.__get_neuron_sdram(
            atoms_per_core, sdram_edge_sdram)

        # Get resources for synapses
        structural_sz = max(
            app_vertex.get_structural_dynamics_size(atoms_per_core),
            BYTES_PER_WORD)
        all_syn_block_sz = max(
            app_vertex.get_synapses_size(atoms_per_core), BYTES_PER_WORD)
        shared_synapse_sdram = self.__get_shared_synapse_sdram(
            atoms_per_core, all_syn_block_sz, structural_sz)
        lead_synapse_core_sdram = self.__get_synapse_sdram(
            atoms_per_core, shared_synapse_sdram)
        shared_synapse_core_sdram = self.__get_synapse_sdram(atoms_per_core)
        synapse_regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        synaptic_matrices = SynapticMatrices(
            app_vertex, synapse_regions, atoms_per_core, weight_scales,
            all_syn_block_sz)
        neuron_data = NeuronData(app_vertex)

        # Keep track of the SDRAM for each group of vertices
        total_sdram = neuron_sdram + lead_synapse_core_sdram
        for _ in range(self.__n_synapse_vertices - 1):
            total_sdram += shared_synapse_core_sdram

        for index, vertex_slice in enumerate(self.__get_fixed_slices()):

            # Create the neuron vertex for the slice
            neuron_vertex = self.__add_neuron_core(
                vertex_slice, neuron_sdram, label, index, rb_shifts,
                weight_scales, neuron_data, atoms_per_core)
            chip_counter.add_core(neuron_sdram)

            # Keep track of synapse vertices for each neuron vertex and
            # resources used by each core (neuron core is added later)
            synapse_vertices = list()
            self.__synapse_verts_by_neuron[neuron_vertex] = synapse_vertices

            # Add the first vertex
            synapse_references, syn_label, feedback_partition = \
                self.__add_lead_synapse_core(
                    vertex_slice, structural_sz, lead_synapse_core_sdram,
                    label, rb_shifts, weight_scales, synapse_vertices,
                    neuron_vertex, atoms_per_core,
                    synaptic_matrices)
            chip_counter.add_core(lead_synapse_core_sdram)

            # Do the remaining synapse cores
            for i in range(1, self.__n_synapse_vertices):
                self.__add_shared_synapse_core(
                    syn_label, i, vertex_slice, synapse_references,
                    shared_synapse_core_sdram, feedback_partition,
                    synapse_vertices, neuron_vertex)
                chip_counter.add_core(shared_synapse_core_sdram)

            # Add resources for Poisson vertices up to core limit
            poisson_vertices = incoming_direct_poisson[vertex_slice]
            # remaining_poisson_vertices = list()
            added_poisson_vertices = list()
            for poisson_vertex, _possion_edge in poisson_vertices:
                added_poisson_vertices.append(poisson_vertex)
                chip_counter.add_core(poisson_vertex.sdram_required)

            # Create an SDRAM edge partition
            source_vertices = added_poisson_vertices + synapse_vertices
            sdram_partition = SourceSegmentedSDRAMMachinePartition(
                SYNAPSE_SDRAM_PARTITION_ID, source_vertices)
            self.__sdram_partitions.append(sdram_partition)
            neuron_vertex.set_sdram_partition(sdram_partition)

            # Add SDRAM edges for synapse vertices
            for source_vertex in source_vertices:
                sdram_partition.add_edge(SDRAMMachineEdge(
                    source_vertex, neuron_vertex,
                    f"SDRAM {source_vertex.label}-->{neuron_vertex.label}"))
                source_vertex.set_sdram_partition(sdram_partition)

            all_vertices = list(source_vertices)
            all_vertices.append(neuron_vertex)
            self.__same_chip_groups.append((all_vertices, total_sdram))

        self.__incoming_vertices = [
            [self.__synapse_verts_by_neuron[neuron][index]
                for neuron in self.__neuron_vertices]
            for index in range(self.__n_synapse_vertices)]

        # Find incoming neuromodulators
        for proj in app_vertex.incoming_projections:
            # pylint: disable=protected-access
            if proj._projection_edge.is_neuromodulation:
                self.__neuromodulators.add(proj._projection_edge.pre_vertex)

    def __add_neuron_core(
            self, vertex_slice, sdram, label, index, rb_shifts,
            weight_scales, neuron_data, atoms_per_core):
        """
        Add a neuron core for for a slice of neurons.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to put on the core
        :param ~pacman.model.resources.MultiRegionSDRAM sdram:
        :param str label: The name to give the core
        :param int index: The index of the slice in the ordered list of slices
        :param list(int) rb_shifts:
            The computed ring-buffer shift values to use to get the weights
            back to S1615 values
        :param list(int) weight_scales:
            The scale to apply to weights to encode them in the 16-bit synapses
        :return: The neuron vertex created and the resources used
        :rtype: PopulationNeuronsMachineVertex
        """
        app_vertex = self.governed_app_vertex
        neuron_vertex = PopulationNeuronsMachineVertex(
            sdram,
            f"{label}_Neurons:{vertex_slice.lo_atom}-{vertex_slice.hi_atom}",
            app_vertex, vertex_slice, index, rb_shifts, weight_scales,
            neuron_data, atoms_per_core)
        app_vertex.remember_machine_vertex(neuron_vertex)
        self.__neuron_vertices.append(neuron_vertex)

        return neuron_vertex

    def __add_lead_synapse_core(
            self, vertex_slice, structural_sz, lead_synapse_core_sdram, label,
            rb_shifts, weight_scales, synapse_vertices, neuron_vertex,
            atoms_per_core, synaptic_matrices):
        """
        Add the first synapse core for a neuron core.  This core will
        generate all the synaptic data required.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons on the neuron core
        :param int lead_synapse_core_sdram:
            The SDRAM that will be used by every lead synapse core
        :param int proj_dependent_sdram:
            The SDRAM that will be used by the synapse core to handle a given
            set of projections
        :param str label: The name to give the core
        :param list(int) rb_shifts:
            The computed ring-buffer shift values to use to get the weights
            back to S1615 values
        :param list(int) weight_scales:
            The scale to apply to weights to encode them in the 16-bit synapses
        :param synapse_vertices: A list to add the core to
        :type synapse_vertices:
            list(~pacman.model.graphs.machine.MachineVertex)
        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex the synapses will feed into
        :param int atoms_per_core: The maximum atoms per core
        :return: References to the synapse regions that can be used by a shared
            synapse core, and the basic label for the synapse cores
        :rtype: tuple(SynapseRegions, str)
        """
        synapse_references = self.__synapse_references
        syn_label = (
            f"{label}_Synapses:{vertex_slice.lo_atom}-{vertex_slice.hi_atom}")

        # Do the lead synapse core
        lead_synapse_vertex = PopulationSynapsesMachineVertexLead(
            lead_synapse_core_sdram, f"{syn_label}(0)",
            self.governed_app_vertex, vertex_slice, rb_shifts, weight_scales,
            structural_sz, synapse_references, atoms_per_core,
            synaptic_matrices)
        self.governed_app_vertex.remember_machine_vertex(lead_synapse_vertex)
        self.__synapse_vertices.append(lead_synapse_vertex)
        synapse_vertices.append(lead_synapse_vertex)

        part = self.__add_plastic_feedback(neuron_vertex, lead_synapse_vertex)

        return synapse_references, syn_label, part

    def __add_shared_synapse_core(
            self, syn_label, s_index, vertex_slice, synapse_references,
            shared_synapse_sdram, feedback_partition, synapse_vertices,
            neuron_vertex):
        """
        Add a second or subsequent synapse core.  This will reference the
        synaptic data generated by the lead synapse core.

        :param str syn_label: The basic synapse core label to be extended
        :param int s_index: The index of the synapse core (0 is the lead core)
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons on the neuron core
        :param SynapseRegions synapse_references:
            References to the synapse regions
        :param ~pacman.model.resources.AbstractSDRAM shared_synapse_sdram:
        :param feedback_partition:
        :param synapse_vertices: A list to add the core to
        :type synapse_vertices:
            list(~pacman.model.graphs.machine.MachineVertex)
        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex the synapses will feed into
        """
        app_vertex = self.governed_app_vertex
        synapse_label = f"{syn_label}({s_index})"
        synapse_vertex = PopulationSynapsesMachineVertexShared(
            shared_synapse_sdram, synapse_label, app_vertex, vertex_slice,
            synapse_references)
        app_vertex.remember_machine_vertex(synapse_vertex)
        self.__synapse_vertices.append(synapse_vertex)
        synapse_vertices.append(synapse_vertex)

        if feedback_partition is not None:
            neuron_to_synapse_edge = MachineEdge(neuron_vertex, synapse_vertex)
            feedback_partition.add_edge(neuron_to_synapse_edge)
            synapse_vertex.set_neuron_vertex_and_partition_id(
                neuron_vertex, SPIKE_PARTITION_ID)

    def __add_plastic_feedback(self, neuron_vertex, synapse_vertex):
        """
        Add an edge if needed from the neuron core back to the synapse core
        to allow the synapse core to process plastic synapses.

        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex to start the edge at
        :param PopulationSynapsesMachineVertexCommon synapse_vertex:
            A synapse vertex to feed the spikes back to
        :rtype: MulticastEdgePartition
        """
        # If synapse dynamics is not simply static, link the neuron vertex
        # back to the synapse vertex
        app_vertex = self.governed_app_vertex
        if (app_vertex.synapse_dynamics is not None and
                not isinstance(app_vertex.synapse_dynamics,
                               SynapseDynamicsStatic)):
            if (app_vertex.self_projection is None):
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
    def __too_many_cores(self):
        incoming = self.governed_app_vertex.incoming_poisson_projections
        return len(incoming) + self.__n_synapse_vertices + 1 > _MAX_CORES

    def __handle_poisson_sources(self, label):
        """
        Go through the incoming projections and find Poisson sources with
        splitters that work with us, and one-to-one connections that will
        then work with SDRAM.

        :param str label: Base label to give to the Poisson cores
        """
        self.__poisson_sources = set()
        incoming_direct_poisson = defaultdict(list)
        # If there are going to be too many to fit on a chip, don't do direct
        # Poisson
        if self.__too_many_cores:
            return incoming_direct_poisson
        for proj in self.governed_app_vertex.incoming_poisson_projections:
            # pylint: disable=protected-access
            pre_vertex = proj._projection_edge.pre_vertex
            conn = proj._synapse_information.connector
            dynamics = proj._synapse_information.synapse_dynamics
            if self.is_direct_poisson_source(pre_vertex, conn, dynamics):
                # Create the direct Poisson vertices here; the splitter
                # for the Poisson will create any others as needed
                for vertex_slice in self.__get_fixed_slices():
                    sdram = pre_vertex.get_sdram_used_by_atoms(vertex_slice)
                    poisson_m_vertex = pre_vertex.create_machine_vertex(
                        vertex_slice, sdram, label=(
                            f"{label}_Poisson:"
                            f"{vertex_slice.lo_atom}-{vertex_slice.hi_atom}"))
                    pre_vertex.remember_machine_vertex(poisson_m_vertex)
                    incoming_direct_poisson[vertex_slice].append(
                        (poisson_m_vertex, proj._projection_edge))

                # Keep track of sources that have been handled
                self.__poisson_sources.add(pre_vertex)
        return incoming_direct_poisson

    @overrides(AbstractSupportsOneToOneSDRAMInput.handles_source_vertex)
    def handles_source_vertex(self, projection):
        # If there are too many incoming Poisson sources, we can't do this
        if self.__too_many_cores:
            return False

        # pylint: disable=protected-access
        edge = projection._projection_edge
        pre_vertex = edge.pre_vertex
        connector = projection._synapse_information.connector
        dynamics = projection._synapse_information.synapse_dynamics
        return self.is_direct_poisson_source(pre_vertex, connector, dynamics)

    def is_direct_poisson_source(self, pre_vertex, connector, dynamics):
        """
        Determine if a given Poisson source can be created by this splitter.

        :param ~pacman.model.graphs.application.ApplicationVertex pre_vertex:
            The vertex sending into the Projection
        :param connector:
            The connector in use in the Projection
        :type connector:
            ~spynnaker.pyNN.models.neural_projections.connectors.AbstractConnector
        :param dynamics:
            The synapse dynamics in use in the Projection
        :type dynamics:
            ~spynnaker.pyNN.models.neuron.synapse_dynamics.AbstractSynapseDynamics
        :rtype: bool
        """
        return (isinstance(pre_vertex, SpikeSourcePoissonVertex) and
                isinstance(pre_vertex.splitter, SplitterPoissonDelegate) and
                len(pre_vertex.outgoing_projections) == 1 and
                isinstance(connector, OneToOneConnector) and
                isinstance(dynamics, SynapseDynamicsStatic))

    def __get_fixed_slices(self):
        """
        Get a list of fixed slices from the Application vertex.

        :rtype: list(~pacman.model.graphs.common.Slice)
        """
        if self.__slices is not None:
            return self.__slices
        self.__slices = get_multidimensional_slices(self.governed_app_vertex)
        return self.__slices

    @overrides(AbstractSplitterCommon.get_in_coming_slices)
    def get_in_coming_slices(self):
        return self.__get_fixed_slices()

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self.__get_fixed_slices()

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, partition_id):
        return self.__neuron_vertices

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(self, partition_id):
        return self.__synapse_vertices

    @overrides(AbstractSplitterCommon.get_source_specific_in_coming_vertices)
    def get_source_specific_in_coming_vertices(
            self, source_vertex, partition_id):
        # If delayed get the real pre-vertex
        if isinstance(source_vertex, DelayExtensionVertex):
            pre_vertex = source_vertex.source_vertex
        else:
            pre_vertex = source_vertex

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
        targets = defaultdict(OrderedSet)
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
        sources_per_vertex = max(1, int(2 ** math.ceil(math.log2(
            n_sources / self.__n_synapse_vertices))))

        # Start on a different index each time to "even things out"
        index = self.__next_synapse_index
        self.__next_synapse_index = (
            (self.__next_synapse_index + 1) % self.__n_synapse_vertices)
        result = list()
        for start in range(0, n_sources, sources_per_vertex):
            end = min(start + sources_per_vertex, n_sources)
            source_range = sources[start:end]
            for s_vertex in self.__incoming_vertices[index]:
                targets_filtered = targets[s_vertex]
                filtered = [s for s in source_range
                            if (s in targets_filtered or
                                s.app_vertex in targets_filtered)]
                result.append((s_vertex, filtered))
            index = (index + 1) % self.__n_synapse_vertices

        return result

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        if self.governed_app_vertex.neuron_recorder.is_recordable(
                variable_to_record):
            return self.__neuron_vertices
        return self.__synapse_vertices

    @overrides(AbstractSplitterCommon.reset_called)
    def reset_called(self):
        self.__neuron_vertices = None
        self.__synapse_vertices = None
        self.__synapse_verts_by_neuron = None
        self.__max_delay = self.__user_max_delay
        if self.__user_max_delay is None:
            # to be calcutaed by __update_max_delay
            self.__expect_delay_extension = None
        else:
            self.__expect_delay_extension = True
        self.__multicast_partitions = []
        self.__sdram_partitions = []
        self.__same_chip_groups = []

    @property
    def n_synapse_vertices(self):
        """
        The number of synapse vertices per neuron vertex.

        :rtype: int
        """
        return self.__n_synapse_vertices

    @property
    def __synapse_references(self):
        """
        The reference identifiers for the shared synapse regions.

        :rtype: SynapseRegions
        """
        references = [
            ReferenceContext.next()
            for _ in range(
                len(PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS))]
        return SynapseRegions(*references)

    def __get_neuron_sdram(self, n_atoms, sdram_edge_sdram):
        """
        Gets the resources of the neurons of a slice of atoms from a given
        application vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self.governed_app_vertex
        n_record = len(app_vertex.neuron_recordables)
        variable_sdram = app_vertex.get_max_neuron_variable_sdram(n_atoms)
        sdram = MultiRegionSDRAM()
        sdram.merge(app_vertex.get_common_constant_sdram(
            n_record, NeuronProvenance.N_ITEMS + NeuronMainProvenance.N_ITEMS,
            PopulationNeuronsMachineVertex.COMMON_REGIONS))
        sdram.merge(app_vertex.get_neuron_constant_sdram(
            n_atoms, PopulationNeuronsMachineVertex.NEURON_REGIONS))
        sdram.add_cost(
            PopulationNeuronsMachineVertex.REGIONS.SDRAM_EDGE_PARAMS.value,
            NEURONS_SDRAM_PARAMS_SIZE)
        sdram.nest(
            len(PopulationNeuronsMachineVertex.REGIONS), variable_sdram)
        sdram.add_cost(
            len(PopulationNeuronsMachineVertex.REGIONS) + 1, sdram_edge_sdram)

        # return the total resources.
        return sdram

    def __shared_synapse_sdram(
            self, independent_synapse_sdram, proj_dependent_sdram,
            all_syn_block_sz, structural_sz, dynamics_sz):
        """
        Get the SDRAM shared between synapse cores.

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
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
            self, n_atoms, all_syn_block_sz, structural_sz):
        independent_synapse_sdram = self.__independent_synapse_sdram()
        proj_dependent_sdram = self.__proj_dependent_synapse_sdram()
        dynamics_sz = self.governed_app_vertex.get_synapse_dynamics_size(
            n_atoms)
        dynamics_sz = max(dynamics_sz, BYTES_PER_WORD)
        return self.__shared_synapse_sdram(
            independent_synapse_sdram, proj_dependent_sdram,
            all_syn_block_sz, structural_sz, dynamics_sz)

    def __get_synapse_sdram(self, n_atoms, shared_sdram=None):
        """
        Get the resources of the synapses of a slice of atoms from a
        given application vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :param ~pacman.model.resources.MultiRegionSDRAM shared_sdram:
            The SDRAM shared between cores, if this is to be included
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self.governed_app_vertex
        n_record = len(app_vertex.synapse_recordables)
        variable_sdram = app_vertex.get_max_synapse_variable_sdram(
            n_atoms)
        sdram = MultiRegionSDRAM()
        sdram.merge(app_vertex.get_common_constant_sdram(
            n_record,
            SynapseProvenance.N_ITEMS + SpikeProcessingFastProvenance.N_ITEMS,
            PopulationSynapsesMachineVertexLead.COMMON_REGIONS))

        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.REGIONS
            .SDRAM_EDGE_PARAMS.value, SYNAPSES_SDRAM_PARAMS_SIZE)
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.REGIONS.KEY_REGION.value,
            KEY_CONFIG_SIZE)
        sdram.nest(
            len(PopulationSynapsesMachineVertexLead.REGIONS) + 1,
            variable_sdram)
        if shared_sdram is not None:
            sdram.merge(shared_sdram)

        # return the total resources.
        return sdram

    def __independent_synapse_sdram(self):
        """
        Get the SDRAM used by all synapse cores independent of projections.

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        app_vertex = self.governed_app_vertex
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            regions.synapse_params,
            max(app_vertex.get_synapse_params_size(), BYTES_PER_WORD))
        return sdram

    def __proj_dependent_synapse_sdram(self):
        """
        Get the SDRAM used by synapse cores dependent on the projections.

        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The projections to consider in the calculations
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self.governed_app_vertex
        regions = PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            regions.pop_table,
            max(MasterPopTableAsBinarySearch.get_master_population_table_size(
                    app_vertex.incoming_projections), BYTES_PER_WORD))
        sdram.add_cost(
            regions.connection_builder,
            max(app_vertex.get_synapse_expander_size(),
                BYTES_PER_WORD))
        sdram.add_cost(
            regions.bitfield_filter,
            max(get_sdram_for_bit_field_region(
                    app_vertex.incoming_projections),
                BYTES_PER_WORD))
        return sdram

    def __update_max_delay(self):
        # Find the maximum delay from incoming synapses
        app_vertex = self.governed_app_vertex
        self.__max_delay, needs_delay_extension = app_vertex.get_max_delay(
            MAX_RING_BUFFER_BITS)
        if self.__user_allow_delay_extension is None:
            self.__expect_delay_extension = needs_delay_extension

    @overrides(AbstractSpynnakerSplitterDelay.max_support_delay)
    def max_support_delay(self):
        if self.__max_delay is None:
            self.__update_max_delay()
        return self.__max_delay

    @overrides(AbstractSpynnakerSplitterDelay.accepts_edges_from_delay_vertex)
    def accepts_edges_from_delay_vertex(self):
        if self.__user_allow_delay_extension is None:
            if self.__expect_delay_extension is None:
                self.__update_max_delay()
            if self.__expect_delay_extension:
                return True
            raise NotImplementedError(
                "This call was unexpected as it was calculated that "
                "the max needed delay was less that the max possible")
        else:
            return self.__user_allow_delay_extension

    @overrides(AbstractSplitterCommon.get_same_chip_groups)
    def get_same_chip_groups(self):
        return self.__same_chip_groups

    @overrides(AbstractSplitterCommon.get_internal_multicast_partitions)
    def get_internal_multicast_partitions(self):
        return self.__multicast_partitions

    @overrides(AbstractSplitterCommon.get_internal_sdram_partitions)
    def get_internal_sdram_partitions(self):
        return self.__sdram_partitions

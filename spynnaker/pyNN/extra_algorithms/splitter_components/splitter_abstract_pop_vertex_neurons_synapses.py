# Copyright (c) 2020-2021 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import math
import logging
from collections import defaultdict
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import (
    ResourceContainer, DTCMResource, CPUCyclesPerTickResource,
    MultiRegionSDRAM)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine import (
    MachineEdge, SourceSegmentedSDRAMMachinePartition, SDRAMMachineEdge,
    MulticastEdgePartition)
from pacman.utilities.algorithm_utilities.\
    partition_algorithm_utilities import get_remaining_constraints
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)
from spynnaker.pyNN.models.neuron import (
    PopulationNeuronsMachineVertex, PopulationSynapsesMachineVertexLead,
    PopulationSynapsesMachineVertexShared, NeuronProvenance, SynapseProvenance,
    AbstractPopulationVertex, SpikeProcessingFastProvenance)
from spynnaker.pyNN.models.neuron.population_neurons_machine_vertex import (
    SDRAM_PARAMS_SIZE as NEURONS_SDRAM_PARAMS_SIZE, NeuronMainProvenance)
from data_specification.reference_context import ReferenceContext
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    SynapseDynamicsStatic, AbstractSynapseDynamicsStructural)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.utility_models.delays import DelayExtensionVertex
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
    get_estimated_sdram_for_bit_field_region,
    get_estimated_sdram_for_key_region,
    exact_sdram_for_bit_field_builder_region)
from .splitter_poisson_delegate import SplitterPoissonDelegate
from .abstract_spynnaker_splitter_delay import AbstractSpynnakerSplitterDelay
from .abstract_supports_one_to_one_sdram_input import (
    AbstractSupportsOneToOneSDRAMInput)

logger = logging.getLogger(__name__)

# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14


class SplitterAbstractPopulationVertexNeuronsSynapses(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay,
        AbstractSupportsOneToOneSDRAMInput):
    """ Splits an AbstractPopulationVertex so that there are separate neuron
        cores each being fed by one or more synapse cores.  Incoming one-to-one
        Poisson cores are also added here if they meet the criteria.
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

    SPLITTER_NAME = "SplitterAbstractPopulationVertexNeuronsSynapses"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopVertexNeuronsSynapses as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

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
            provided, and this is given as None, it will be computed based on
            whether delay extensions should be needed.
        :type allow_delay_extension: bool or None
        """
        super(SplitterAbstractPopulationVertexNeuronsSynapses, self).__init__(
            self.SPLITTER_NAME)
        AbstractSpynnakerSplitterDelay.__init__(self)
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

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, chip_counter):
        app_vertex = self._governed_app_vertex
        label = app_vertex.label
        constraints = get_remaining_constraints(app_vertex)

        # Structural plasticity can only be run on a single synapse core
        if (isinstance(app_vertex.synapse_dynamics,
                       AbstractSynapseDynamicsStructural) and
                self.__n_synapse_vertices != 1):
            raise SynapticConfigurationException(
                "The current implementation of structural plasticity can only"
                " be run on a single synapse core.  Please ensure the number"
                " of synapse cores is set to 1")

        # Do some checks to make sure everything is likely to fit
        atoms_per_core = min(
            app_vertex.get_max_atoms_per_core(), app_vertex.n_atoms)
        n_synapse_types = app_vertex.neuron_impl.get_n_synapse_types()
        if (get_n_bits(atoms_per_core) + get_n_bits(n_synapse_types) +
                get_n_bits(self.max_support_delay())) > MAX_RING_BUFFER_BITS:
            raise SynapticConfigurationException(
                "The combination of the number of neurons per core ({}), "
                "the number of synapse types ({}), and the maximum delay per "
                "core ({}) will require too much DTCM.  Please reduce one or "
                "more of these values.".format(
                    atoms_per_core, n_synapse_types, self.max_support_delay()))

        self.__neuron_vertices = list()
        self.__synapse_vertices = list()
        self.__synapse_verts_by_neuron = defaultdict(list)

        incoming_direct_poisson = self.__handle_poisson_sources(label)

        # Work out the ring buffer shifts based on all incoming things
        rb_shifts = app_vertex.get_ring_buffer_shifts(
            app_vertex.incoming_projections)
        weight_scales = app_vertex.get_weight_scales(rb_shifts)

        # We add the SDRAM edge SDRAM to the neuron resources so it is
        # accounted for within the placement
        n_incoming = self.__n_synapse_vertices + len(self.__poisson_sources)
        edge_sdram = PopulationNeuronsMachineVertex.get_n_bytes_for_transfer(
            atoms_per_core, n_synapse_types)
        sdram_edge_sdram = edge_sdram * n_incoming

        # Get maximum resources for neurons for each split
        neuron_resources = self.__get_neuron_resources(
            atoms_per_core, sdram_edge_sdram)

        # Get resources for synapses
        structural_sz = max(
            app_vertex.get_structural_dynamics_size(
                atoms_per_core, app_vertex.incoming_projections),
            BYTES_PER_WORD)
        all_syn_block_sz = max(app_vertex.get_synapses_size(
            atoms_per_core, app_vertex.incoming_projections), BYTES_PER_WORD)
        shared_synapse_sdram = self.__get_shared_synapse_sdram(
            atoms_per_core, all_syn_block_sz, structural_sz)
        lead_synapse_resources = self.__get_synapse_resources(
            atoms_per_core, shared_synapse_sdram)
        shared_synapse_resources = self.__get_synapse_resources(atoms_per_core)

        # Keep track of the SDRAM for each group of vertices
        total_sdram = neuron_resources.sdram + lead_synapse_resources.sdram
        for _ in range(self.__n_synapse_vertices - 1):
            total_sdram += shared_synapse_resources.sdram

        for index, vertex_slice in enumerate(self.__get_fixed_slices()):

            # Create the neuron vertex for the slice
            neuron_vertex = self.__add_neuron_core(
                vertex_slice, neuron_resources, label, index, rb_shifts,
                weight_scales, constraints)
            chip_counter.add_core(neuron_resources)

            # Keep track of synapse vertices for each neuron vertex and
            # resources used by each core (neuron core is added later)
            synapse_vertices = list()
            self.__synapse_verts_by_neuron[neuron_vertex] = synapse_vertices

            # Add the first vertex
            synapse_references, syn_label, feedback_partition = \
                self.__add_lead_synapse_core(
                    vertex_slice, all_syn_block_sz, structural_sz,
                    lead_synapse_resources, label, rb_shifts, weight_scales,
                    synapse_vertices, neuron_vertex, constraints)
            chip_counter.add_core(lead_synapse_resources)

            # Do the remaining synapse cores
            for i in range(1, self.__n_synapse_vertices):
                self.__add_shared_synapse_core(
                    syn_label, i, vertex_slice, synapse_references,
                    shared_synapse_resources, feedback_partition,
                    synapse_vertices, neuron_vertex, constraints)
                chip_counter.add_core(shared_synapse_resources)

            # Add resources for Poisson vertices up to core limit
            poisson_vertices = incoming_direct_poisson[vertex_slice]
            # remaining_poisson_vertices = list()
            added_poisson_vertices = list()
            for poisson_vertex, _possion_edge in poisson_vertices:
                added_poisson_vertices.append(poisson_vertex)
                chip_counter.add_core(poisson_vertex.resources_required)

            # Create an SDRAM edge partition
            source_vertices = added_poisson_vertices + synapse_vertices
            sdram_partition = SourceSegmentedSDRAMMachinePartition(
                SYNAPSE_SDRAM_PARTITION_ID, source_vertices)
            self.__sdram_partitions.append(sdram_partition)
            neuron_vertex.set_sdram_partition(sdram_partition)

            # Add SDRAM edges for synapse vertices
            for source_vertex in source_vertices:
                edge_label = "SDRAM {}-->{}".format(
                    source_vertex.label, neuron_vertex.label)
                sdram_partition.add_edge(
                    SDRAMMachineEdge(source_vertex, neuron_vertex, edge_label))
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
            if proj._projection_edge.is_neuromodulation:
                self.__neuromodulators.add(proj._projection_edge.pre_vertex)

    def __add_neuron_core(
            self, vertex_slice, neuron_resources, label, index, rb_shifts,
            weight_scales, constraints):
        """ Add a neuron core for for a slice of neurons

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to put on the core
        :param str label: The name to give the core
        :param int index: The index of the slice in the ordered list of slices
        :param list(int) rb_shifts:
            The computed ring-buffer shift values to use to get the weights
            back to S1615 values
        :param list(int) weight_scales:
            The scale to apply to weights to encode them in the 16-bit synapses
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints to add
        :return: The neuron vertex created and the resources used
        :rtype: tuple(PopulationNeuronsMachineVertex, \
                      ~pacman.model.resources.ResourceContainer)
        """
        app_vertex = self._governed_app_vertex
        neuron_label = "{}_Neurons:{}-{}".format(
            label, vertex_slice.lo_atom, vertex_slice.hi_atom)
        neuron_vertex = PopulationNeuronsMachineVertex(
            neuron_resources, neuron_label, constraints, app_vertex,
            vertex_slice, index, rb_shifts, weight_scales)
        app_vertex.remember_machine_vertex(neuron_vertex)
        self.__neuron_vertices.append(neuron_vertex)

        return neuron_vertex

    def __add_lead_synapse_core(
            self, vertex_slice, all_syn_block_sz, structural_sz,
            lead_synapse_resources, label, rb_shifts, weight_scales,
            synapse_vertices, neuron_vertex, constraints):
        """ Add the first synapse core for a neuron core.  This core will
            generate all the synaptic data required.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons on the neuron core
        :param int independent_synapse_sdram:
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
        :param list(~pacman.model.resources.ResourceContainer) all_resources:
            A list to add the resources of the vertex to
        :param list(~pacman.model.graphs.machine.MachineVertex) \
                synapse_vertices:
            A list to add the core to
        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex the synapses will feed into
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints to add
        :return: References to the synapse regions that can be used by a shared
            synapse core, and the basic label for the synapse cores
        :rtype: tuple(SynapseRegions, str)
        """
        synapse_references = self.__synapse_references
        syn_label = "{}_Synapses:{}-{}".format(
            label, vertex_slice.lo_atom, vertex_slice.hi_atom)

        # Do the lead synapse core
        lead_synapse_vertex = PopulationSynapsesMachineVertexLead(
            lead_synapse_resources, "{}(0)".format(syn_label), constraints,
            self._governed_app_vertex, vertex_slice, rb_shifts, weight_scales,
            all_syn_block_sz, structural_sz, synapse_references)
        self._governed_app_vertex.remember_machine_vertex(lead_synapse_vertex)
        self.__synapse_vertices.append(lead_synapse_vertex)
        synapse_vertices.append(lead_synapse_vertex)

        part = self.__add_plastic_feedback(neuron_vertex, lead_synapse_vertex)

        return synapse_references, syn_label, part

    def __add_shared_synapse_core(
            self, syn_label, s_index, vertex_slice, synapse_references,
            shared_synapse_resources, feedback_partition, synapse_vertices,
            neuron_vertex, constraints):
        """ Add a second or subsequent synapse core.  This will reference the
            synaptic data generated by the lead synapse core.

        :param str syn_label: The basic synapse core label to be extended
        :param int s_index: The index of the synapse core (0 is the lead core)
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons on the neuron core
        :param SynapseRegions synapse_references:
            References to the synapse regions
        :param list(~pacman.model.resources.ResourceContainer) all_resources:
            A list to add the resources of the vertex to
        :param list(~pacman.model.graphs.machine.MachineVertex) \
                synapse_vertices:
            A list to add the core to
        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex the synapses will feed into
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints to add
        """
        app_vertex = self._governed_app_vertex
        synapse_label = "{}({})".format(syn_label, s_index)
        synapse_vertex = PopulationSynapsesMachineVertexShared(
            shared_synapse_resources, synapse_label, constraints, app_vertex,
            vertex_slice, synapse_references)
        app_vertex.remember_machine_vertex(synapse_vertex)
        self.__synapse_vertices.append(synapse_vertex)
        synapse_vertices.append(synapse_vertex)

        if feedback_partition is not None:
            neuron_to_synapse_edge = MachineEdge(neuron_vertex, synapse_vertex)
            feedback_partition.add_edge(neuron_to_synapse_edge)
            synapse_vertex.set_neuron_vertex_and_partition_id(
                neuron_vertex, SPIKE_PARTITION_ID)

    def __add_plastic_feedback(self, neuron_vertex, synapse_vertex):
        """ Add an edge if needed from the neuron core back to the synapse core
            to allow the synapse core to process plastic synapses

        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex to start the edge at
        :param PopulationSynapsesMachineVertexCommon synapse_vertex:
            A synapse vertex to feed the spikes back to
        :rtype: MulticastEdgePartition
        """

        # If synapse dynamics is not simply static, link the neuron vertex
        # back to the synapse vertex
        app_vertex = self._governed_app_vertex
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

    def __handle_poisson_sources(self, label):
        """ Go through the incoming projections and find Poisson sources with
            splitters that work with us, and one-to-one connections that will
            then work with SDRAM

        :param str label: Base label to give to the Poisson cores
        """
        self.__poisson_sources = set()
        incoming_direct_poisson = defaultdict(list)
        for proj in self._governed_app_vertex.incoming_projections:
            # pylint: disable=protected-access
            pre_vertex = proj._projection_edge.pre_vertex
            conn = proj._synapse_information.connector
            dynamics = proj._synapse_information.synapse_dynamics
            if self.is_direct_poisson_source(pre_vertex, conn, dynamics):
                # Create the direct Poisson vertices here; the splitter
                # for the Poisson will create any others as needed
                for vertex_slice in self.__get_fixed_slices():
                    resources = pre_vertex.get_resources_used_by_atoms(
                        vertex_slice)
                    poisson_label = "{}_Poisson:{}-{}".format(
                        label, vertex_slice.lo_atom, vertex_slice.hi_atom)
                    poisson_m_vertex = pre_vertex.create_machine_vertex(
                        vertex_slice, resources, label=poisson_label)
                    pre_vertex.remember_machine_vertex(poisson_m_vertex)
                    incoming_direct_poisson[vertex_slice].append(
                        (poisson_m_vertex, proj._projection_edge))

                # Keep track of sources that have been handled
                self.__poisson_sources.add(pre_vertex)
        return incoming_direct_poisson

    @staticmethod
    def is_direct_poisson_source(pre_vertex, connector, dynamics):
        """ Determine if a given Poisson source can be created by this splitter

        :param ~pacman.model.graphs.application.ApplicationVertex pre_vertex:
            The vertex sending into the Projection
        :param ~spynnaker.pyNN.models.neural_projections.connectors\
                .AbstractConnector:
            The connector in use in the Projection
        :param ~spynnaker.pyNN.models.neuron.synapse_dynamics\
                .AbstractSynapseDynamics:
            The synapse dynamics in use in the Projection
        :rtype: bool
        """
        return (isinstance(pre_vertex, SpikeSourcePoissonVertex) and
                isinstance(pre_vertex.splitter, SplitterPoissonDelegate) and
                len(pre_vertex.outgoing_projections) == 1 and
                isinstance(connector, OneToOneConnector) and
                isinstance(dynamics, SynapseDynamicsStatic))

    def __get_fixed_slices(self):
        """ Get a list of fixed slices from the Application vertex

        :rtype: list(~pacman.model.graphs.common.Slice)
        """
        if self.__slices is not None:
            return self.__slices
        atoms_per_core = self._governed_app_vertex.get_max_atoms_per_core()
        n_atoms = self._governed_app_vertex.n_atoms
        self.__slices = [Slice(low, min(low + atoms_per_core - 1, n_atoms - 1))
                         for low in range(0, n_atoms, atoms_per_core)]
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
        # If the edge is delayed, get the real edge
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

        # Split the incoming machine vertices so that they are in ~power of 2
        # groups
        sources = source_vertex.splitter.get_out_going_vertices(partition_id)
        n_sources = len(sources)
        if n_sources < self.__n_synapse_vertices:
            sources_per_vertex = 1
        else:
            sources_per_vertex = int(2 ** math.ceil(math.log(
                n_sources / self.__n_synapse_vertices)))

        # Start on a different index each time to "even things out"
        index = self.__next_synapse_index
        self.__next_synapse_index = (
            (self.__next_synapse_index + 1) % self.__n_synapse_vertices)
        result = list()
        for start in range(0, n_sources, sources_per_vertex):
            end = min(start + sources_per_vertex, n_sources)
            source_range = sources[start:end]
            for s_vertex in self.__incoming_vertices[index]:
                result.append((s_vertex, source_range))
            index = (index + 1) % self.__n_synapse_vertices

        return result

    @overrides(AbstractSplitterCommon.machine_vertices_for_recording)
    def machine_vertices_for_recording(self, variable_to_record):
        if self._governed_app_vertex.neuron_recorder.is_recordable(
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
        """ Return the number of synapse vertices per neuron vertex

        :rtype: int
        """
        return self.__n_synapse_vertices

    @property
    def __synapse_references(self):
        """ Get reference identifiers for the shared synapse regions

        :rtype: SynapseRegions
        """
        references = [
            ReferenceContext.next()
            for _ in range(
                len(PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS))]
        return SynapseRegions(*references)

    def __get_neuron_resources(self, n_atoms, sdram_edge_sdram):
        """  Gets the resources of the neurons of a slice of atoms from a given
             app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        app_vertex = self._governed_app_vertex
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

        dtcm = app_vertex.get_common_dtcm()
        dtcm += app_vertex.get_neuron_dtcm(n_atoms)
        cpu_cycles = app_vertex.get_common_cpu()
        cpu_cycles += app_vertex.get_neuron_cpu(n_atoms)

        # set resources required from this object
        container = ResourceContainer(
            sdram=sdram, dtcm=DTCMResource(dtcm),
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles))

        # return the total resources.
        return container

    def __shared_synapse_sdram(
            self, independent_synapse_sdram, proj_dependent_sdram,
            all_syn_block_sz, structural_sz, dynamics_sz):
        """ Get the SDRAM shared between synapse cores

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        sdram = MultiRegionSDRAM()
        sdram.merge(independent_synapse_sdram)
        sdram.merge(proj_dependent_sdram)
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .synaptic_matrix, all_syn_block_sz)
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS.direct_matrix,
            max(self._governed_app_vertex.all_single_syn_size, BYTES_PER_WORD))
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .structural_dynamics, structural_sz)
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .synapse_dynamics, dynamics_sz)
        return sdram

    def __get_shared_synapse_sdram(
            self, n_atoms, all_syn_block_sz, structural_sz):
        app_vertex = self._governed_app_vertex
        independent_synapse_sdram = self.__independent_synapse_sdram()
        proj_dependent_sdram = self.__proj_dependent_synapse_sdram(
            app_vertex.incoming_projections)
        dynamics_sz = self._governed_app_vertex.get_synapse_dynamics_size(
            n_atoms)
        dynamics_sz = max(dynamics_sz, BYTES_PER_WORD)
        return self.__shared_synapse_sdram(
            independent_synapse_sdram, proj_dependent_sdram,
            all_syn_block_sz, structural_sz, dynamics_sz)

    def __get_synapse_resources(self, n_atoms, shared_sdram=None):
        """  Get the resources of the synapses of a slice of atoms from a
             given app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :param ~pacman.model.resources.MultiRegionSDRAM shared_sdram:
            The SDRAM shared between cores, if this is to be included
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        app_vertex = self._governed_app_vertex
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
        dtcm = app_vertex.get_common_dtcm()
        dtcm += app_vertex.get_synapse_dtcm(n_atoms)
        cpu_cycles = app_vertex.get_common_cpu()
        cpu_cycles += app_vertex.get_synapse_cpu(n_atoms)

        # set resources required from this object
        container = ResourceContainer(
            sdram=sdram, dtcm=DTCMResource(dtcm),
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles))

        # return the total resources.
        return container

    def __independent_synapse_sdram(self):
        """ Get the SDRAM used by all synapse cores independent of projections

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self._governed_app_vertex
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS.synapse_params,
            max(app_vertex.get_synapse_params_size(), BYTES_PER_WORD))
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .bitfield_builder,
            max(exact_sdram_for_bit_field_builder_region(), BYTES_PER_WORD))
        return sdram

    def __proj_dependent_synapse_sdram(self, incoming_projections):
        """ Get the SDRAM used by synapse cores dependent on the projections

        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The projections to consider in the calculations
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        app_vertex = self._governed_app_vertex
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS.pop_table,
            max(MasterPopTableAsBinarySearch.get_master_population_table_size(
                    incoming_projections), BYTES_PER_WORD))
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .connection_builder,
            max(app_vertex.get_synapse_expander_size(incoming_projections),
                BYTES_PER_WORD))
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .bitfield_filter,
            max(get_estimated_sdram_for_bit_field_region(incoming_projections),
                BYTES_PER_WORD))
        sdram.add_cost(
            PopulationSynapsesMachineVertexLead.SYNAPSE_REGIONS
            .bitfield_key_map,
            max(get_estimated_sdram_for_key_region(incoming_projections),
                BYTES_PER_WORD))
        return sdram

    def __update_max_delay(self):
        # Find the maximum delay from incoming synapses
        app_vertex = self._governed_app_vertex
        max_delay_ms = 0
        for proj in app_vertex.incoming_projections:
            # pylint: disable=protected-access
            s_info = proj._synapse_information
            proj_max_delay = s_info.synapse_dynamics.get_delay_maximum(
                s_info.connector, s_info)
            max_delay_ms = max(max_delay_ms, proj_max_delay)
        max_delay_steps = math.ceil(max_delay_ms / machine_time_step_ms())
        max_delay_bits = get_n_bits(max_delay_steps)

        # Find the maximum possible delay
        n_atom_bits = get_n_bits(min(
            app_vertex.get_max_atoms_per_core(), app_vertex.n_atoms))
        n_synapse_bits = get_n_bits(
            app_vertex.neuron_impl.get_n_synapse_types())
        n_delay_bits = MAX_RING_BUFFER_BITS - (n_atom_bits + n_synapse_bits)

        # Pick the smallest between the two, so that not too many bits are used
        final_n_delay_bits = min(n_delay_bits, max_delay_bits)
        self.__max_delay = 2 ** final_n_delay_bits
        if self.__user_allow_delay_extension is None:
            self.__expect_delay_extension = max_delay_bits > final_n_delay_bits

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

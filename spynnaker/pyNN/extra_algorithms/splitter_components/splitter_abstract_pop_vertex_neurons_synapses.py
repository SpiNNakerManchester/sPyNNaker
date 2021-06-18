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
    MachineEdge, SourceSegmentedSDRAMMachinePartition, SDRAMMachineEdge)
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
from spinn_front_end_common.utilities.exceptions import ConfigurationException
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
from spynnaker.pyNN.models.neural_projections import DelayedApplicationEdge
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
        # Any application edges from Poisson sources that are handled here
        "__poisson_edges",
        # The maximum delay supported
        "__max_delay",
        # The user-set maximum delay, for reset
        "__user_max_delay",
        # Whether to allow delay extensions to be created
        "__allow_delay_extension",
        # The user-set allowing of delay extensions
        "__user_allow_delay_extension",
        # The fixed slices the vertices are divided into
        "__slices",
        # The next synapse core to use for an incoming machine edge
        "__next_synapse_index"]

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
        self.__allow_delay_extension = allow_delay_extension
        self.__user_allow_delay_extension = allow_delay_extension
        self.__slices = None
        self.__next_synapse_index = 0

        if (self.__max_delay is not None and
                self.__allow_delay_extension is None):
            self.__allow_delay_extension = True

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
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
                get_n_bits(self.__get_max_delay)) > MAX_RING_BUFFER_BITS:
            raise SynapticConfigurationException(
                "The combination of the number of neurons per core ({}), "
                "the number of synapse types ({}), and the maximum delay per "
                "core ({}) will require too much DTCM.  Please reduce one or "
                "more of these values.".format(
                    atoms_per_core, n_synapse_types, self.__get_max_delay))

        self.__neuron_vertices = list()
        self.__synapse_vertices = list()
        self.__synapse_verts_by_neuron = defaultdict(list)

        incoming_direct_poisson = self.__handle_poisson_sources(
            label, machine_graph)

        # Work out the ring buffer shifts based on all incoming things
        rb_shifts = app_vertex.get_ring_buffer_shifts(
            app_vertex.incoming_projections)
        weight_scales = app_vertex.get_weight_scales(rb_shifts)

        # Get resources for synapses
        independent_synapse_sdram = self.__independent_synapse_sdram()
        proj_dependent_sdram = self.__proj_dependent_synapse_sdram(
            app_vertex.incoming_projections)

        for index, vertex_slice in enumerate(self.__get_fixed_slices()):

            # Find the maximum number of cores on any chip available
            max_crs = resource_tracker.get_maximum_cores_available_on_a_chip()
            if max_crs < (self.__n_synapse_vertices + 1):
                raise ConfigurationException(
                    "No chips remaining with enough cores for"
                    f" {self.__n_synapse_vertices} synapse cores and a neuron"
                    " core")
            max_crs -= self.__n_synapse_vertices + 1

            # Create the neuron vertex for the slice
            neuron_vertex, neuron_resources = self.__add_neuron_core(
                vertex_slice, label, index, rb_shifts, weight_scales,
                machine_graph, constraints)

            # Keep track of synapse vertices for each neuron vertex and
            # resources used by each core (neuron core is added later)
            synapse_vertices = list()
            self.__synapse_verts_by_neuron[neuron_vertex] = synapse_vertices
            all_resources = []

            # Add the first vertex
            synapse_references, syn_label = self.__add_lead_synapse_core(
                vertex_slice, independent_synapse_sdram, proj_dependent_sdram,
                label, rb_shifts, weight_scales, all_resources, machine_graph,
                synapse_vertices, neuron_vertex, constraints)

            # Do the remaining synapse cores
            for i in range(1, self.__n_synapse_vertices):
                self.__add_shared_synapse_core(
                    syn_label, i, vertex_slice, synapse_references,
                    all_resources, machine_graph, synapse_vertices,
                    neuron_vertex, constraints)

            # Add resources for Poisson vertices up to core limit
            poisson_vertices = incoming_direct_poisson[vertex_slice]
            remaining_poisson_vertices = list()
            added_poisson_vertices = list()
            for poisson_vertex, poisson_edge in poisson_vertices:
                if max_crs <= 0:
                    remaining_poisson_vertices.append(poisson_vertex)
                    self.__add_poisson_multicast(
                        poisson_vertex, synapse_vertices, machine_graph,
                        poisson_edge)
                else:
                    all_resources.append(
                        (poisson_vertex.resources_required, []))
                    added_poisson_vertices.append(poisson_vertex)
                    max_crs -= 1

            if remaining_poisson_vertices:
                logger.warn(
                    f"Vertex {label} is using multicast for"
                    f" {len(remaining_poisson_vertices)} one-to-one Poisson"
                    " sources as not enough cores exist to put them on the"
                    " same chip")

            # Create an SDRAM edge partition
            sdram_label = "SDRAM {} Synapses-->Neurons:{}-{}".format(
                label, vertex_slice.lo_atom, vertex_slice.hi_atom)
            source_vertices = added_poisson_vertices + synapse_vertices
            sdram_partition = SourceSegmentedSDRAMMachinePartition(
                SYNAPSE_SDRAM_PARTITION_ID, sdram_label, source_vertices)
            machine_graph.add_outgoing_edge_partition(sdram_partition)
            neuron_vertex.set_sdram_partition(sdram_partition)

            # Add SDRAM edges for synapse vertices
            for source_vertex in source_vertices:
                edge_label = "SDRAM {}-->{}".format(
                    source_vertex.label, neuron_vertex.label)
                machine_graph.add_edge(
                    SDRAMMachineEdge(
                        source_vertex, neuron_vertex, edge_label),
                    SYNAPSE_SDRAM_PARTITION_ID)
                source_vertex.set_sdram_partition(sdram_partition)

            # Add SDRAM edge requirements to the neuron SDRAM, as the resource
            # tracker will otherwise try to add another core for it
            extra_sdram = MultiRegionSDRAM()
            extra_sdram.merge(neuron_resources.sdram)
            extra_sdram.add_cost(
                len(extra_sdram.regions) + 1,
                sdram_partition.total_sdram_requirements())
            neuron_resources_plus = ResourceContainer(
                sdram=extra_sdram, dtcm=neuron_resources.dtcm,
                cpu_cycles=neuron_resources.cpu_cycles,
                iptags=neuron_resources.iptags,
                reverse_iptags=neuron_resources.reverse_iptags)
            all_resources.append((neuron_resources_plus, constraints))

            # Allocate all the resources to ensure they all fit
            resource_tracker.allocate_constrained_group_resources(
                all_resources)

        return True

    def __add_poisson_multicast(
            self, poisson_vertex, synapse_vertices, machine_graph, app_edge):
        """ Add an edge from a one-to-one Poisson source to one of the
            synapse vertices using multicast

        :param MachineVertex poisson_vertex:
            The Poisson machine vertex to use as a source
        :param list(MachineVertex) synapse_vertices:
            The list of synapse vertices that can be used as targets
        :param MachineGraph machine_graph: The machine graph to add the edge to
        :param ProjectionEdge app_edge: The application edge of the connection
        """
        post_vertex = synapse_vertices[self.__next_synapse_index]
        self.__next_synapse_index = (
            (self.__next_synapse_index + 1) % self.__n_synapse_vertices)
        edge = MachineEdge(poisson_vertex, post_vertex, app_edge=app_edge,
                           label=f"Machine edge for {app_edge.label}")
        machine_graph.add_edge(edge, SPIKE_PARTITION_ID)

    def __add_neuron_core(
            self, vertex_slice, label, index, rb_shifts, weight_scales,
            machine_graph, constraints):
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
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph to add the core to
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints to add
        :return: The neuron vertex created and the resources used
        :rtype: tuple(PopulationNeuronsMachineVertex, \
                      ~pacman.model.resources.ResourceContainer)
        """
        app_vertex = self._governed_app_vertex
        neuron_resources = self.__get_neuron_resources(vertex_slice)
        neuron_label = "{}_Neurons:{}-{}".format(
            label, vertex_slice.lo_atom, vertex_slice.hi_atom)
        neuron_vertex = PopulationNeuronsMachineVertex(
            neuron_resources, neuron_label, constraints, app_vertex,
            vertex_slice, index, rb_shifts, weight_scales)
        machine_graph.add_vertex(neuron_vertex)
        self.__neuron_vertices.append(neuron_vertex)

        return neuron_vertex, neuron_resources

    def __add_lead_synapse_core(
            self, vertex_slice, independent_synapse_sdram,
            proj_dependent_sdram, label, rb_shifts, weight_scales,
            all_resources, machine_graph, synapse_vertices, neuron_vertex,
            constraints):
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
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph to add the core to
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
        # Get common synapse resources
        app_vertex = self._governed_app_vertex
        structural_sz = app_vertex.get_structural_dynamics_size(
                vertex_slice, app_vertex.incoming_projections)
        dynamics_sz = self._governed_app_vertex.get_synapse_dynamics_size(
            vertex_slice)
        all_syn_block_sz = app_vertex.get_synapses_size(
                    vertex_slice, app_vertex.incoming_projections)
        # Need a minimum size to make it possible to reference
        structural_sz = max(structural_sz, BYTES_PER_WORD)
        dynamics_sz = max(dynamics_sz, BYTES_PER_WORD)
        all_syn_block_sz = max(all_syn_block_sz, BYTES_PER_WORD)
        shared_sdram = self.__shared_synapse_sdram(
            independent_synapse_sdram, proj_dependent_sdram,
            all_syn_block_sz, structural_sz, dynamics_sz)
        synapse_references = self.__synapse_references
        syn_label = "{}_Synapses:{}-{}".format(
            label, vertex_slice.lo_atom, vertex_slice.hi_atom)

        # Do the lead synapse core
        lead_synapse_resources = self.__get_synapse_resources(
            vertex_slice, shared_sdram)
        lead_synapse_vertex = PopulationSynapsesMachineVertexLead(
            lead_synapse_resources, "{}(0)".format(syn_label), constraints,
            app_vertex, vertex_slice, rb_shifts, weight_scales,
            all_syn_block_sz, structural_sz, synapse_references)
        all_resources.append((lead_synapse_resources, constraints))
        machine_graph.add_vertex(lead_synapse_vertex)
        self.__synapse_vertices.append(lead_synapse_vertex)
        synapse_vertices.append(lead_synapse_vertex)

        self.__add_plastic_feedback(
            machine_graph, neuron_vertex, lead_synapse_vertex)

        return synapse_references, syn_label

    def __add_shared_synapse_core(
            self, syn_label, s_index, vertex_slice, synapse_references,
            all_resources, machine_graph, synapse_vertices,
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
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph to add the core to
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
        synapse_resources = self.__get_synapse_resources(vertex_slice)
        synapse_vertex = PopulationSynapsesMachineVertexShared(
            synapse_resources, synapse_label, constraints, app_vertex,
            vertex_slice, synapse_references)
        all_resources.append((synapse_resources, constraints))
        machine_graph.add_vertex(synapse_vertex)
        self.__synapse_vertices.append(synapse_vertex)
        synapse_vertices.append(synapse_vertex)

        self.__add_plastic_feedback(
            machine_graph, neuron_vertex, synapse_vertex)

    def __add_plastic_feedback(
            self, machine_graph, neuron_vertex, synapse_vertex):
        """ Add an edge if needed from the neuron core back to the synapse core
            to allow the synapse core to process plastic synapses

        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph to add the core to
        :param PopulationNeuronsMachineVertex neuron_vertex:
            The neuron vertex to start the edge at
        :param PopulationSynapsesMachineVertexCommon synapse_vertex:
            A synapse vertex to feed the spikes back to
        """

        # If synapse dynamics is not simply static, link the neuron vertex
        # back to the synapse vertex
        app_vertex = self._governed_app_vertex
        if (app_vertex.synapse_dynamics is not None and
                not isinstance(app_vertex.synapse_dynamics,
                               SynapseDynamicsStatic) and
                app_vertex.self_projection is None):
            neuron_to_synapse_edge = MachineEdge(neuron_vertex, synapse_vertex)
            machine_graph.add_edge(neuron_to_synapse_edge, SPIKE_PARTITION_ID)
            synapse_vertex.set_neuron_to_synapse_edge(neuron_to_synapse_edge)

    def __handle_poisson_sources(self, label, machine_graph):
        """ Go through the incoming projections and find Poisson sources with
            splitters that work with us, and one-to-one connections that will
            then work with SDRAM

        :param str label: Base label to give to the Poisson cores
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
            The graph to add any Poisson cores to
        """
        self.__poisson_edges = set()
        incoming_direct_poisson = defaultdict(list)
        for proj in self._governed_app_vertex.incoming_projections:
            pre_vertex = proj._projection_edge.pre_vertex
            connector = proj._synapse_information.connector
            if self.__is_direct_poisson_source(pre_vertex, connector):
                # Create the direct Poisson vertices here; the splitter
                # for the Poisson will create any others as needed
                for vertex_slice in self.__get_fixed_slices():
                    resources = pre_vertex.get_resources_used_by_atoms(
                        vertex_slice)
                    poisson_label = "{}_Poisson:{}-{}".format(
                        label, vertex_slice.lo_atom, vertex_slice.hi_atom)
                    poisson_m_vertex = pre_vertex.create_machine_vertex(
                        vertex_slice, resources, label=poisson_label)
                    machine_graph.add_vertex(poisson_m_vertex)
                    incoming_direct_poisson[vertex_slice].append(
                        (poisson_m_vertex, proj._projection_edge))

                # Keep track of edges that have been used for this
                self.__poisson_edges.add(proj._projection_edge)
        return incoming_direct_poisson

    def __is_direct_poisson_source(self, pre_vertex, connector):
        """ Determine if a given Poisson source can be created by this splitter

        :param ~pacman.model.graphs.application.ApplicationVertex pre_vertex:
            The vertex sending into the Projection
        :param ~spynnaker.pyNN.models.neural_projections.connectors\
                .AbstractConnector:
            The connector in use in the Projection
        :rtype: bool
        """
        return (isinstance(pre_vertex, SpikeSourcePoissonVertex) and
                isinstance(pre_vertex.splitter, SplitterPoissonDelegate) and
                len(pre_vertex.outgoing_projections) == 1 and
                isinstance(connector, OneToOneConnector))

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
        return self.__get_fixed_slices(), True

    @overrides(AbstractSplitterCommon.get_out_going_slices)
    def get_out_going_slices(self):
        return self.__get_fixed_slices(), True

    @overrides(AbstractSplitterCommon.get_out_going_vertices)
    def get_out_going_vertices(self, edge, outgoing_edge_partition):
        return {v: [MachineEdge] for v in self.__neuron_vertices}

    @overrides(AbstractSplitterCommon.get_in_coming_vertices)
    def get_in_coming_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        # If the edge is delayed, get the real edge
        if isinstance(edge, DelayedApplicationEdge):
            edge = edge.undelayed_edge

        # Filter out edges from Poisson sources being done using SDRAM
        if edge in self.__poisson_edges:
            return {}

        # Pick the same synapse vertex index for each neuron vertex
        index = self.__next_synapse_index
        self.__next_synapse_index = (
            (self.__next_synapse_index + 1) % self.__n_synapse_vertices)
        return {self.__synapse_verts_by_neuron[neuron][index]: [MachineEdge]
                for neuron in self.__neuron_vertices}

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
        self.__allow_delay_extension = self.__user_allow_delay_extension

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

    def __get_neuron_resources(self, vertex_slice):
        """  Gets the resources of the neurons of a slice of atoms from a given
             app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        n_record = len(self._governed_app_vertex.neuron_recordables)
        variable_sdram = self._governed_app_vertex.get_neuron_variable_sdram(
            vertex_slice)
        sdram = MultiRegionSDRAM()
        sdram.merge(self._governed_app_vertex.get_common_constant_sdram(
            n_record, NeuronProvenance.N_ITEMS + NeuronMainProvenance.N_ITEMS,
            PopulationNeuronsMachineVertex.COMMON_REGIONS))
        sdram.merge(self._governed_app_vertex.get_neuron_constant_sdram(
            vertex_slice, PopulationNeuronsMachineVertex.NEURON_REGIONS))
        sdram.add_cost(
            PopulationNeuronsMachineVertex.REGIONS.SDRAM_EDGE_PARAMS.value,
            NEURONS_SDRAM_PARAMS_SIZE)
        sdram.nest(
            len(PopulationNeuronsMachineVertex.REGIONS) + 1, variable_sdram)
        dtcm = self._governed_app_vertex.get_common_dtcm()
        dtcm += self._governed_app_vertex.get_neuron_dtcm(vertex_slice)
        cpu_cycles = self._governed_app_vertex.get_common_cpu()
        cpu_cycles += self._governed_app_vertex.get_neuron_cpu(vertex_slice)

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

    def __get_synapse_resources(self, vertex_slice, shared_sdram=None):
        """  Get the resources of the synapses of a slice of atoms from a
             given app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :param ~pacman.model.resources.MultiRegionSDRAM shared_sdram:
            The SDRAM shared between cores, if this is to be included
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        n_record = len(self._governed_app_vertex.synapse_recordables)
        variable_sdram = self._governed_app_vertex.get_synapse_variable_sdram(
            vertex_slice)
        sdram = MultiRegionSDRAM()
        sdram.merge(self._governed_app_vertex.get_common_constant_sdram(
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
        dtcm = self._governed_app_vertex.get_common_dtcm()
        dtcm += self._governed_app_vertex.get_synapse_dtcm(vertex_slice)
        cpu_cycles = self._governed_app_vertex.get_common_cpu()
        cpu_cycles += self._governed_app_vertex.get_synapse_cpu(vertex_slice)

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

    @property
    def __get_max_delay(self):
        if self.__max_delay is not None:
            return self.__max_delay

        # Find the maximum delay from incoming synapses
        app_vertex = self._governed_app_vertex
        max_delay_ms = 0
        for proj in app_vertex.incoming_projections:
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
        if self.__allow_delay_extension is None:
            self.__allow_delay_extension = max_delay_bits > final_n_delay_bits
        return self.__max_delay

    @overrides(AbstractSpynnakerSplitterDelay.max_support_delay)
    def max_support_delay(self):
        return self.__get_max_delay

    @overrides(AbstractSpynnakerSplitterDelay.accepts_edges_from_delay_vertex)
    def accepts_edges_from_delay_vertex(self):
        if self.__allow_delay_extension is None:
            self.__get_max_delay
        return self.__allow_delay_extension

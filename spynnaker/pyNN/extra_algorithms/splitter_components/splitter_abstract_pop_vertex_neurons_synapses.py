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
from collections import defaultdict
import numpy
from spinn_utilities.overrides import overrides
from pacman.exceptions import PacmanConfigurationException
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, DTCMResource, CPUCyclesPerTickResource)
from pacman.model.partitioner_splitters.abstract_splitters import (
    AbstractSplitterCommon)
from pacman.model.graphs.common.slice import Slice
from pacman.model.graphs.machine import (
    MachineEdge, SourceSegmentedSDRAMMachinePartition, SDRAMMachineEdge)
from spynnaker.pyNN.models.neuron import (
    PopulationNeuronsMachineVertex, PopulationSynapsesMachineVertex,
    NeuronProvenance, SynapseProvenance, AbstractPopulationVertex)
from spynnaker.pyNN.utilities.constants import SYNAPSE_SDRAM_PARTITION_ID
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

# The maximum number of bits for the ring buffer index that are likely to
# fit in DTCM (14-bits = 16,384 16-bit ring buffer entries = 32Kb DTCM
MAX_RING_BUFFER_BITS = 14


class SplitterAbstractPopulationVertexNeuronsSynapses(
        AbstractSplitterCommon, AbstractSpynnakerSplitterDelay,
        AbstractSupportsOneToOneSDRAMInput):
    """ handles the splitting of the AbstractPopulationVertex via slice logic.
    """

    __slots__ = [
        "__neuron_vertices",
        "__synapse_vertices",
        "__synapse_verts_by_neuron",
        "__synapse_verts_for_edge",
        "__n_synapse_vertices",
        "__poisson_edges",
        "__max_delay",
        "__allow_delay_extension",
        "__slices"]

    SPLITTER_NAME = "SplitterAbstractPopulationVertexNeuronsSynapses"

    INVALID_POP_ERROR_MESSAGE = (
        "The vertex {} cannot be supported by the "
        "SplitterAbstractPopVertexNeuronsSynapses as"
        " the only vertex supported by this splitter is a "
        "AbstractPopulationVertex. Please use the correct splitter for "
        "your vertex and try again.")

    def __init__(self, n_synapse_vertices=1,
                 max_delay=(AbstractSpynnakerSplitterDelay
                            .MAX_SUPPORTED_DELAY_TICS),
                 allow_delay_extension=True):
        super(SplitterAbstractPopulationVertexNeuronsSynapses, self).__init__(
            self.SPLITTER_NAME)
        AbstractSpynnakerSplitterDelay.__init__(self)
        self.__n_synapse_vertices = n_synapse_vertices
        self.__max_delay = max_delay
        self.__allow_delay_extension = allow_delay_extension
        self.__slices = None

    @overrides(AbstractSplitterCommon.set_governed_app_vertex)
    def set_governed_app_vertex(self, app_vertex):
        AbstractSplitterCommon.set_governed_app_vertex(self, app_vertex)
        if not isinstance(app_vertex, AbstractPopulationVertex):
            raise PacmanConfigurationException(
                self.INVALID_POP_ERROR_MESSAGE.format(app_vertex))

    @overrides(AbstractSplitterCommon.create_machine_vertices)
    def create_machine_vertices(self, resource_tracker, machine_graph):
        # Do some checks to make sure everything is likely to fit
        atoms_per_core = min(
            self._governed_app_vertex.get_max_atoms_per_core(),
            self._governed_app_vertex.n_atoms)
        n_synapse_types = (
            self._governed_app_vertex.neuron_impl.get_n_synapse_types())
        if (get_n_bits(atoms_per_core) + get_n_bits(n_synapse_types) +
                get_n_bits(self.__max_delay)) > MAX_RING_BUFFER_BITS:
            raise SynapticConfigurationException(
                "The combination of the number of neurons per core ({}), "
                "the number of synapse types ({}), and the maximum delay per "
                "core ({}) will require too much DTCM.  Please reduce one or "
                "more of these values.".format(
                    atoms_per_core, n_synapse_types, self.__max_delay))

        label = self._governed_app_vertex.label
        self.__poisson_edges = set()

        # Go through the incoming projections and find Poisson sources with
        # splitters that work with us, and one-to-one connections that will
        # then work with SDRAM
        incoming_direct_poisson = defaultdict(list)
        for proj in self._governed_app_vertex.incoming_projections:
            pre_vertex = proj._projection_edge.pre_vertex
            connector = proj._synapse_information.connector
            if (isinstance(pre_vertex, SpikeSourcePoissonVertex) and
                isinstance(pre_vertex.splitter, SplitterPoissonDelegate) and
                    len(pre_vertex.outgoing_projections) == 1 and
                    isinstance(connector, OneToOneConnector)):

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
                        poisson_m_vertex)

                # Keep track of edges that have been used for this
                self.__poisson_edges.add(proj._projection_edge)

        # Distribute the projections between each synapse core
        projections_by_index = self.distribute_projections()

        # Work out the maximum shift for each synapse type and use that
        # everywhere for consistency
        app_vertex = self._governed_app_vertex
        rb_shift_by_index = [app_vertex.get_ring_buffer_shifts(projs)
                             for projs in projections_by_index]
        max_rb_shifts = numpy.amax(rb_shift_by_index, axis=0)
        weight_scales = app_vertex.get_weight_scales(max_rb_shifts)

        # Get resources for synapses
        independent_sdram = self.__independent_synapse_sdram()
        proj_dependent_sdram = [self.__proj_dependent_synapse_sdram(projs)
                                for projs in projections_by_index]

        self.__neuron_vertices = list()
        self.__synapse_vertices = list()
        self.__synapse_verts_by_neuron = defaultdict(list)
        self.__synapse_verts_for_edge = defaultdict(list)
        for vertex_slice in self.__get_fixed_slices():

            # Create the neuron an synapse vertices
            neuron_resources = self.__get_neuron_resources(vertex_slice)
            all_resources = [neuron_resources]
            neuron_label = "{}_Neurons:{}-{}".format(
                label, vertex_slice.lo_atom, vertex_slice.hi_atom)
            neuron_vertex = PopulationNeuronsMachineVertex(
                neuron_resources, neuron_label, None, app_vertex, vertex_slice,
                max_rb_shifts, weight_scales)
            machine_graph.add_vertex(neuron_vertex)
            self.__neuron_vertices.append(neuron_vertex)
            synapse_vertices = list()
            self.__synapse_verts_by_neuron[neuron_vertex] = synapse_vertices
            for i in range(self.__n_synapse_vertices):
                synapse_label = "{}_Synapses:{}-{}({})".format(
                    label, vertex_slice.lo_atom, vertex_slice.hi_atom, i)
                projs = projections_by_index[i]
                proj_sdram = proj_dependent_sdram[i]
                structural_sz = app_vertex.get_structural_dynamics_size(
                    vertex_slice, projs)
                all_syn_block_sz = app_vertex.get_synapses_size(
                    vertex_slice, projs)
                synapse_resources = self.__get_synapse_resources(
                    independent_sdram, proj_sdram, all_syn_block_sz,
                    structural_sz, vertex_slice, projs)
                synapse_vertex = PopulationSynapsesMachineVertex(
                    synapse_resources, synapse_label, None, app_vertex,
                    vertex_slice, max_rb_shifts, weight_scales,
                    all_syn_block_sz, structural_sz)
                all_resources.append(synapse_resources)
                machine_graph.add_vertex(synapse_vertex)
                self.__synapse_vertices.append(synapse_vertex)
                synapse_vertices.append(synapse_vertex)
                for proj in projs:
                    app_edge = proj._projection_edge
                    self.__synapse_verts_for_edge[app_edge].append(
                        synapse_vertex)

            # Add resources for Poisson vertices
            poisson_vertices = incoming_direct_poisson[vertex_slice]
            for poisson_vertex in poisson_vertices:
                all_resources.append(poisson_vertex.resources_required)

            # Create an SDRAM edge partition
            sdram_label = "SDRAM {} Synapses-->Neurons:{}-{}".format(
                label, vertex_slice.lo_atom, vertex_slice.hi_atom)
            source_vertices = poisson_vertices + synapse_vertices
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
            neuron_resources.extend(ResourceContainer(sdram=ConstantSDRAM(
                sdram_partition.total_sdram_requirements())))

            # Allocate all the resources to ensure they all fit
            resource_tracker.allocate_group_resources(all_resources)

        return True

    def distribute_projections(self):
        """ Distribute the projections between the synapse vertices.  Allows
            for overriding of just this method to get different behaviour.
            The default is to distribute between synapse cores in round-robin.

        :return: A list of projections for each of n_synapse_vertices
        :rtype: list(list(PyNNProjectionCommon))
        """
        projections_by_index = [[] for _ in range(self.__n_synapse_vertices)]
        index = 0
        for proj in self._governed_app_vertex.incoming_projections:
            projections_by_index[index].append(proj)
            index = (index + 1) % self.__n_synapse_vertices
        return projections_by_index

    def __get_fixed_slices(self):
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
        # Filter out edges from Poisson sources being done using SDRAM
        if edge in self.__poisson_edges:
            return {}
        if edge not in self.__synapse_verts_for_edge:
            raise SynapticConfigurationException(
                "Unexpected incoming edge: {}".format(edge))
        return {v: [MachineEdge]
                for v in self.__synapse_verts_for_edge[edge]}

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

    def __get_neuron_resources(self, vertex_slice):
        """  Gets the resources of the neurons of a slice of atoms from a given
             app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        n_record = len(self._governed_app_vertex.neuron_recordables)
        variable_sdram = self._governed_app_vertex.get_neuron_variable_sdram(
            vertex_slice)
        constant_sdram = self._governed_app_vertex.get_common_constant_sdram(
            n_record, NeuronProvenance.N_ITEMS)
        constant_sdram += self._governed_app_vertex.get_neuron_constant_sdram(
            vertex_slice)
        dtcm = self._governed_app_vertex.get_common_dtcm()
        dtcm += self._governed_app_vertex.get_neuron_dtcm(vertex_slice)
        cpu_cycles = self._governed_app_vertex.get_common_cpu()
        cpu_cycles += self._governed_app_vertex.get_neuron_cpu(vertex_slice)

        # set resources required from this object
        container = ResourceContainer(
            sdram=variable_sdram + ConstantSDRAM(constant_sdram),
            dtcm=DTCMResource(dtcm),
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles))

        # return the total resources.
        return container

    def __get_synapse_resources(
            self, independent_sdram, proj_dependent_sdram, all_syn_block_sz,
            structural_sz, vertex_slice, incoming_projections):
        """  Gets the resources of the synapses of a slice of atoms from a
             given app vertex.

        :param ~pacman.model.graphs.common.Slice vertex_slice: the slice
        :rtype: ~pacman.model.resources.ResourceContainer
        """
        n_record = len(self._governed_app_vertex.synapse_recordables)
        variable_sdram = self._governed_app_vertex.get_synapse_variable_sdram(
            vertex_slice)
        constant_sdram = self._governed_app_vertex.get_common_constant_sdram(
            n_record, SynapseProvenance.N_ITEMS)
        constant_sdram += independent_sdram + proj_dependent_sdram
        constant_sdram += all_syn_block_sz + structural_sz
        constant_sdram += self._governed_app_vertex.get_synapse_dynamics_size(
            vertex_slice)
        dtcm = self._governed_app_vertex.get_common_dtcm()
        dtcm += self._governed_app_vertex.get_synapse_dtcm(vertex_slice)
        cpu_cycles = self._governed_app_vertex.get_common_cpu()
        cpu_cycles += self._governed_app_vertex.get_synapse_cpu(vertex_slice)

        # set resources required from this object
        container = ResourceContainer(
            sdram=variable_sdram + ConstantSDRAM(constant_sdram),
            dtcm=DTCMResource(dtcm),
            cpu_cycles=CPUCyclesPerTickResource(cpu_cycles))

        # return the total resources.
        return container

    def __independent_synapse_sdram(self):
        app_vertex = self._governed_app_vertex
        return (
            app_vertex.get_synapse_params_size() +
            exact_sdram_for_bit_field_builder_region())

    def __proj_dependent_synapse_sdram(self, incoming_projections):
        app_vertex = self._governed_app_vertex
        return (
            MasterPopTableAsBinarySearch.get_master_population_table_size(
                incoming_projections) +
            app_vertex.get_synapse_expander_size(incoming_projections) +
            get_estimated_sdram_for_bit_field_region(incoming_projections) +
            get_estimated_sdram_for_key_region(incoming_projections))

    @overrides(AbstractSpynnakerSplitterDelay.max_support_delay)
    def max_support_delay(self):
        return self.__max_delay

    @overrides(AbstractSpynnakerSplitterDelay.accepts_edges_from_delay_vertex)
    def accepts_edges_from_delay_vertex(self):
        return self.__allow_delay_extension

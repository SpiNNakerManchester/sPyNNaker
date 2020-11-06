# Copyright (c) 2017-2019 The University of Manchester
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
import logging
import math
from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.model.constraints.partitioner_constraints import (
    SameAtomsAsVertexConstraint)
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractGeneratesDataSpecification,
    AbstractProvidesOutgoingPartitionConstraints)
from spinn_front_end_common.abstract_models.impl import (
    TDMAAwareApplicationVertex)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES, BITS_PER_WORD,
    BYTES_PER_WORD)
from .delay_block import DelayBlock
from .delay_extension_machine_vertex import DelayExtensionMachineVertex
from .delay_generator_data import DelayGeneratorData
from spynnaker.pyNN.utilities.constants import (
    SPIKE_PARTITION_ID, POP_TABLE_MAX_ROW_LENGTH)
from spynnaker.pyNN.models.neural_projections import DelayedApplicationEdge
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractGenerateConnectorOnMachine)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractGenerateOnMachine)

logger = logging.getLogger(__name__)

#  1. has_key 2. key 3. incoming_key 4. incoming_mask 5. n_atoms
#  6. n_delay_stages
_DELAY_PARAM_HEADER_WORDS = 6
# pylint: disable=protected-access
_DELEXT_REGIONS = DelayExtensionMachineVertex._DELAY_EXTENSION_REGIONS
_EXPANDER_BASE_PARAMS_SIZE = 3 * BYTES_PER_WORD

# The microseconds per timestep will be divided by this for the max offset
_MAX_OFFSET_DENOMINATOR = 10


class DelayExtensionVertex(
        TDMAAwareApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractProvidesOutgoingPartitionConstraints):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """
    __slots__ = [
        "__delay_blocks",
        "__delay_per_stage",
        "__machine_time_step",
        "__n_atoms",
        "__n_delay_stages",
        "__source_vertex",
        "__time_scale_factor",
        "__delay_generator_data",
        "__n_subvertices",
        "__n_data_specs"]

    ESTIMATED_CPU_CYCLES = 128

    def __init__(self, n_neurons, delay_per_stage, source_vertex,
                 machine_time_step, time_scale_factor, constraints=None,
                 label="DelayExtension"):
        """
        :param int n_neurons: the number of neurons
        :param int delay_per_stage: the delay per stage
        :param ~pacman.model.graphs.application.ApplicationVertex \
                source_vertex:
            where messages are coming from
        :param int machine_time_step: how long is the machine time step
        :param int time_scale_factor: what slowdown factor has been applied
        :param iterable(~pacman.model.constraints.AbstractConstraint) \
                constraints:
            the vertex constraints
        :param str label: the vertex label
        """
        # pylint: disable=too-many-arguments
        super(DelayExtensionVertex, self).__init__(
            label, constraints, POP_TABLE_MAX_ROW_LENGTH)

        self.__source_vertex = source_vertex
        self.__n_delay_stages = 0
        self.__delay_per_stage = delay_per_stage
        self.__delay_generator_data = defaultdict(list)
        self.__machine_time_step = machine_time_step
        self.__time_scale_factor = time_scale_factor
        self.__n_subvertices = 0
        self.__n_data_specs = 0

        # atom store
        self.__n_atoms = n_neurons

        # Dictionary of vertex_slice -> delay block for data specification
        self.__delay_blocks = dict()

        self.add_constraint(
            SameAtomsAsVertexConstraint(source_vertex))

    @overrides(TDMAAwareApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        self.__n_subvertices += 1
        return DelayExtensionMachineVertex(
            resources_required, label, constraints, self, vertex_slice)

    @inject_items({
        "graph": "MemoryApplicationGraph"})
    @overrides(TDMAAwareApplicationVertex.get_resources_used_by_atoms,
               additional_arguments={"graph"})
    def get_resources_used_by_atoms(self, vertex_slice, graph):
        """
        :param ~pacman.model.graphs.application.ApplicationGraph graph:
        """
        # pylint: disable=arguments-differ
        out_edges = graph.get_edges_starting_at_vertex(self)
        return ResourceContainer(
            sdram=ConstantSDRAM(
                self.get_sdram_usage_for_atoms(out_edges)),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms(vertex_slice)))

    @property
    @overrides(TDMAAwareApplicationVertex.n_atoms)
    def n_atoms(self):
        return self.__n_atoms

    @property
    def n_delay_stages(self):
        """ The maximum number of delay stages required by any connection\
            out of this delay extension vertex

        :rtype: int
        """
        return self.__n_delay_stages

    @n_delay_stages.setter
    def n_delay_stages(self, n_delay_stages):
        self.__n_delay_stages = n_delay_stages

    @property
    def source_vertex(self):
        """
        :rtype: ~pacman.model.graphs.application.ApplicationVertex
        """
        return self.__source_vertex

    def add_delays(self, vertex_slice, source_ids, stages):
        """ Add delayed connections for a given vertex slice

        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param list(int) source_ids:
        :param list(int) stages:
        """
        if vertex_slice not in self.__delay_blocks:
            self.__delay_blocks[vertex_slice] = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        for (source_id, stage) in zip(source_ids, stages):
            self.__delay_blocks[vertex_slice].add_delay(source_id, stage)

    def add_generator_data(
            self, max_row_n_synapses, max_delayed_row_n_synapses, pre_slices,
            post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_information, max_stage):
        """ Add delays for a connection to be generated

        :param int max_row_n_synapses:
            The maximum number of synapses in a row
        :param int max_delayed_row_n_synapses:
            The maximum number of synapses in a delay row
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
            The list of slices of the pre application vertex
        :param list(~pacman.model.graphs.common.Slice) post_slices:
            The list of slices of the post application vertex
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
            The slice of the pre applcation vertex currently being
            considered
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
            The slice of the post application vertex currently being
            considered
        :param ~spynnaker.pyNN.models.neural_projections.SynapseInformation \
                synapse_information:
            The synapse information of the connection
        :param int max_stage:
            The maximum delay stage
        """
        self.__delay_generator_data[pre_vertex_slice].append(
            DelayGeneratorData(
                max_row_n_synapses, max_delayed_row_n_synapses,
                pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
                synapse_information, max_stage, self.__machine_time_step))

    @inject_items({
        "machine_graph": "MemoryMachineGraph",
        "routing_infos": "MemoryRoutingInfos"})
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={"machine_graph", "routing_infos"})
    def generate_data_specification(
            self, spec, placement, machine_graph, routing_infos):
        """
        :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        :param ~pacman.model.routing_info.RoutingInfo routing_infos:
        """
        # pylint: disable=arguments-differ

        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = vertex.vertex_slice
        n_words_per_stage = int(
            math.ceil(vertex_slice.n_atoms / BITS_PER_WORD))
        delay_params_sz = BYTES_PER_WORD * (
            _DELAY_PARAM_HEADER_WORDS +
            (self.__n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.SYSTEM.value,
            size=SIMULATION_N_BYTES, label='setup')

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        spec.reserve_memory_region(
            region=_DELEXT_REGIONS.TDMA_REGION.value,
            size=self.tdma_sdram_size_in_bytes, label="tdma data")

        # reserve region for provenance
        vertex.reserve_provenance_data_region(spec)

        self._write_setup_info(
            spec, self.__machine_time_step, self.__time_scale_factor,
            vertex.get_binary_file_name())

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = routing_infos.get_first_key_from_pre_vertex(
            vertex, SPIKE_PARTITION_ID)

        incoming_key = 0
        incoming_mask = 0
        incoming_edges = machine_graph.get_edges_ending_at_vertex(
            vertex)

        for incoming_edge in incoming_edges:
            incoming_slice = incoming_edge.pre_vertex.vertex_slice
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                r_info = routing_infos.get_routing_info_for_edge(incoming_edge)
                incoming_key = r_info.first_key
                incoming_mask = r_info.first_mask

        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask)

        if vertex_slice in self.__delay_generator_data:
            generator_data = self.__delay_generator_data[vertex_slice]
            expander_size = sum(data.size for data in generator_data)
            expander_size += _EXPANDER_BASE_PARAMS_SIZE
            spec.reserve_memory_region(
                region=_DELEXT_REGIONS.EXPANDER_REGION.value,
                size=expander_size, label='delay_expander')
            spec.switch_write_focus(_DELEXT_REGIONS.EXPANDER_REGION.value)
            spec.write_value(len(generator_data))
            spec.write_value(vertex_slice.lo_atom)
            spec.write_value(vertex_slice.n_atoms)
            for data in generator_data:
                spec.write_array(data.gen_data)

        # add tdma data
        spec.switch_write_focus(_DELEXT_REGIONS.TDMA_REGION.value)
        spec.write_array(self.generate_tdma_data_specification_data(
            self.vertex_slices.index(vertex_slice)))

        # End-of-Spec:
        spec.end_specification()

    def _write_setup_info(
            self, spec, machine_time_step, time_scale_factor, binary_name):
        """
        :param ~data_specification.DataSpecificationGenerator spec:
        :param int machine_time_step:v the machine time step
        :param int time_scale_factor: the time scale factor
        :param str binary_name: the binary name
        """
        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(_DELEXT_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            binary_name, machine_time_step, time_scale_factor))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask):
        """ Generate Delay Parameter data

        :param ~data_specification.DataSpecificationGenerator spec:
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int key:
        :param int incoming_key:
        :param int incoming_mask:
        """
        # pylint: disable=too-many-arguments

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(_DELEXT_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core and the incoming key and mask:
        if key is None:
            spec.write_value(0)
            spec.write_value(0)
        else:
            spec.write_value(1)
            spec.write_value(data=key)
        spec.write_value(data=incoming_key)
        spec.write_value(data=incoming_mask)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self.__n_delay_stages)

        # Write the actual delay blocks (create a new one if it doesn't exist)
        if vertex_slice in self.__delay_blocks:
            delay_block = self.__delay_blocks[vertex_slice]
        else:
            delay_block = DelayBlock(
                self.__n_delay_stages, self.__delay_per_stage, vertex_slice)
        spec.write_array(array_values=delay_block.delay_block)

    def get_cpu_usage_for_atoms(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: int
        """
        return self.ESTIMATED_CPU_CYCLES * vertex_slice.n_atoms

    def get_sdram_usage_for_atoms(self, out_edges):
        """
        :param list(.ApplicationEdge) out_edges:
        :rtype: int
        """
        return (
            SYSTEM_BYTES_REQUIREMENT + self.tdma_sdram_size_in_bytes +
            DelayExtensionMachineVertex.get_provenance_data_size(
                DelayExtensionMachineVertex.N_EXTRA_PROVENANCE_DATA_ENTRIES) +
            self._get_size_of_generator_information(out_edges))

    def _get_edge_generator_size(self, synapse_info):
        """ Get the size of the generator data for a given synapse info object

        :param SynapseInformation synapse_info:
        """
        connector = synapse_info.connector
        dynamics = synapse_info.synapse_dynamics
        connector_gen = isinstance(
            connector, AbstractGenerateConnectorOnMachine) and \
            connector.generate_on_machine(
                synapse_info.weights, synapse_info.delays)
        synapse_gen = isinstance(
            dynamics, AbstractGenerateOnMachine)
        if connector_gen and synapse_gen:
            return sum((
                DelayGeneratorData.BASE_SIZE,
                connector.gen_delay_params_size_in_bytes(
                    synapse_info.delays),
                connector.gen_connector_params_size_in_bytes,
            ))
        return 0

    def _get_size_of_generator_information(self, out_edges):
        """ Get the size of the generator data for all edges

        :param list(.ApplicationEdge) out_edges:
        :rtype: int
        """
        gen_on_machine = False
        size = 0
        for out_edge in out_edges:
            if isinstance(out_edge, DelayedApplicationEdge):
                for synapse_info in out_edge.synapse_information:

                    # Get the number of likely vertices
                    max_atoms = out_edge.post_vertex.get_max_atoms_per_core()
                    if out_edge.post_vertex.n_atoms < max_atoms:
                        max_atoms = out_edge.post_vertex.n_atoms
                    n_edge_vertices = int(math.ceil(float(
                        out_edge.post_vertex.n_atoms) / float(max_atoms)))

                    # Get the size
                    gen_size = self._get_edge_generator_size(synapse_info)
                    if gen_size > 0:
                        gen_on_machine = True
                        size += gen_size * n_edge_vertices
        if gen_on_machine:
            size += _EXPANDER_BASE_PARAMS_SIZE
        return size

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :rtype: int
        """
        words_per_atom = 11 + 16
        return words_per_atom * BYTES_PER_WORD * vertex_slice.n_atoms

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [ContiguousKeyRangeContraint()]

    def delay_generator_data(self, vertex_slice):
        if vertex_slice in self.__delay_generator_data:
            return self.__delay_generator_data[vertex_slice]
        else:
            return None

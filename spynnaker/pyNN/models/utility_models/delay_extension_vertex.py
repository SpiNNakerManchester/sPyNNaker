import logging
import math
import random

from spinn_front_end_common.utilities import constants as common_constants

from pacman.executor.injection_decorator import requires_injection, inject, \
    supports_injection
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application.impl.application_vertex import \
    ApplicationVertex
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.sdram_resource import SDRAMResource

from spinn_front_end_common.abstract_models\
    .abstract_provides_n_keys_for_partition \
    import AbstractProvidesNKeysForPartition
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.abstract_models.impl.uses_simulation_data_specable_vertex import \
    UsesSimulationDataSpecableVertex

from spynnaker.pyNN.models.utility_models.delay_block import DelayBlock
from spynnaker.pyNN.models.utility_models.delay_extension_machine_vertex \
    import DelayExtensionMachineVertex
from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)

_DELAY_PARAM_HEADER_WORDS = 7
_DEFAULT_MALLOCS_USED = 2


@supports_injection
class DelayExtensionVertex(
        ApplicationVertex, UsesSimulationDataSpecableVertex,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesNKeysForPartition):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """

    _n_vertices = 0

    def __init__(self, n_neurons, delay_per_stage, source_vertex,
                 machine_time_step, timescale_factor, constraints=None,
                 label="DelayExtension"):
        """
        Creates a new DelayExtension Object.
        """
        ApplicationVertex.__init__(self, label, constraints, 256)
        UsesSimulationDataSpecableVertex.__init__(
            self, machine_time_step, timescale_factor)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractProvidesNKeysForPartition.__init__(self)

        self._source_vertex = source_vertex
        self._n_delay_stages = 0
        self._delay_per_stage = delay_per_stage

        # storage params
        self._graph_mapper = None
        self._machine_graph = None
        self._routing_info = None

        # atom store
        self._n_atoms = n_neurons

        # Dictionary of vertex_slice -> delay block for data specification
        self._delay_blocks = dict()

        self.add_constraint(
            PartitionerSameSizeAsVertexConstraint(source_vertex))

    @overrides(ApplicationVertex.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        DelayExtensionVertex._n_vertices += 1
        return DelayExtensionMachineVertex(
            resources_required, label, constraints)

    @overrides(ApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice):
        return ResourceContainer(
            sdram=SDRAMResource(
                self.get_sdram_usage_for_atoms()),
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms(vertex_slice)),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms(vertex_slice)))

    @property
    @overrides(ApplicationVertex.n_atoms)
    def n_atoms(self):
        return self._n_atoms

    @property
    @overrides(ApplicationVertex.model_name)
    def model_name(self):
        return "DelayExtension"

    @property
    def n_delay_stages(self):
        """ The maximum number of delay stages required by any connection
            out of this delay extension vertex
        """
        return self._n_delay_stages

    @n_delay_stages.setter
    def n_delay_stages(self, n_delay_stages):
        self._n_delay_stages = n_delay_stages

    @property
    def source_vertex(self):
        return self._source_vertex

    def add_delays(self, vertex_slice, source_ids, stages):
        """ Add delayed connections for a given vertex slice
        """
        key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if key not in self._delay_blocks:
            self._delay_blocks[key] = DelayBlock(
                self._n_delay_stages, self._delay_per_stage, vertex_slice)
        [self._delay_blocks[key].add_delay(source_id, stage)
            for (source_id, stage) in zip(source_ids, stages)]

    @requires_injection([
        "MemoryMachineGraph", "MemoryRoutingInfos", "MemoryGraphMapper"])
    @overrides(UsesSimulationDataSpecableVertex.generate_data_specification)
    def generate_data_specification(self, spec, placement):

        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = self._graph_mapper.get_slice(vertex)
        n_words_per_stage = int(math.ceil(vertex_slice.n_atoms / 32.0))
        delay_params_sz = \
            4 * (_DELAY_PARAM_HEADER_WORDS +
                 (self._n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=(
                DelayExtensionMachineVertex.
                _DELAY_EXTENSION_REGIONS.SYSTEM.value),
            size=common_constants.SYSTEM_BYTES_REQUIREMENT,
            label='setup')

        spec.reserve_memory_region(
            region=(
                DelayExtensionMachineVertex.
                _DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value),
            size=delay_params_sz, label='delay_params')

        vertex.reserve_provenance_data_region(spec)

        self.write_setup_info(spec)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = self._routing_info.get_first_key_from_pre_vertex(
            vertex, constants.SPIKE_PARTITION_ID)

        incoming_key = None
        incoming_mask = None
        incoming_edges = self._machine_graph.get_edges_ending_at_vertex(
            vertex)

        for incoming_edge in incoming_edges:
            incoming_slice = self._graph_mapper.get_slice(
                incoming_edge.pre_vertex)
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                r_info = \
                    self._routing_info.get_routing_info_for_edge(incoming_edge)
                incoming_key = r_info.first_key
                incoming_mask = r_info.first_mask

        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask,
            self._n_vertices)

        # End-of-Spec:
        spec.end_specification()

    def write_setup_info(self, spec):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(
            DelayExtensionMachineVertex.
                _DELAY_EXTENSION_REGIONS.SYSTEM.value)
        spec.write_array(self.data_for_simulation_data())


    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask,
            n_vertices):
        """ Generate Delay Parameter data
        """

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            region=(
                DelayExtensionMachineVertex.
                _DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value))

        # Write header info to the memory region:
        # Write Key info for this core and the incoming key and mask:
        spec.write_value(data=key)
        spec.write_value(data=incoming_key)
        spec.write_value(data=incoming_mask)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self._n_delay_stages)

        # Write the random back off value
        spec.write_value(random.randint(0, n_vertices))

        # Write the time between spikes
        spikes_per_timestep = self._n_delay_stages * vertex_slice.n_atoms
        time_between_spikes = (
            (self._machine_time_step * self._time_scale_factor) /
            (spikes_per_timestep * 2.0))
        spec.write_value(data=int(time_between_spikes))

        # Write the actual delay blocks
        spec.write_array(array_values=self._delay_blocks[(
            vertex_slice.lo_atom, vertex_slice.hi_atom)].delay_block)

    def get_cpu_usage_for_atoms(self, vertex_slice):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self):
        size_of_mallocs = (
            _DEFAULT_MALLOCS_USED *
            common_constants.SARK_PER_MALLOC_SDRAM_USAGE)
        return (
            size_of_mallocs + common_constants.SYSTEM_BYTES_REQUIREMENT +
            DelayExtensionMachineVertex.get_provenance_data_size(0))

    def get_dtcm_usage_for_atoms(self, vertex_slice):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    @overrides(UsesSimulationDataSpecableVertex.get_binary_file_name)
    def get_binary_file_name(self):
        return "delay_extension.aplx"

    def get_n_keys_for_partition(self, partition, graph_mapper):
        vertex_slice = graph_mapper.get_slice(
            partition.edges[0].pre_vertex)
        if self._n_delay_stages == 0:
            return 1
        return vertex_slice.n_atoms * self._n_delay_stages

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [KeyAllocatorContiguousRangeContraint()]

    @inject("MemoryGraphMapper")
    def set_graph_mapper(self, graph_mapper):
        self._graph_mapper = graph_mapper

    @inject("MemoryMachineGraph")
    def set_machine_graph(self, machine_graph):
        self._machine_graph = machine_graph

    @inject("MemoryRoutingInfos")
    def set_routing_info(self, routing_info):
        self._routing_info = routing_info


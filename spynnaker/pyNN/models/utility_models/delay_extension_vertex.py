import logging
import math
import random

from spinn_front_end_common.utilities import constants as common_constants

from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.constraints.partitioner_constraints \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import CPUCyclesPerTickResource, DTCMResource
from pacman.model.resources import ResourceContainer, SDRAMResource

from spinn_front_end_common.abstract_models\
    .abstract_provides_n_keys_for_partition \
    import AbstractProvidesNKeysForPartition
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities.utility_objs.executable_start_type \
    import ExecutableStartType

from spynnaker.pyNN.models.utility_models.delay_block import DelayBlock
from spinn_front_end_common.abstract_models\
    .abstract_generates_data_specification \
    import AbstractGeneratesDataSpecification
from spinn_front_end_common.abstract_models.abstract_has_associated_binary \
    import AbstractHasAssociatedBinary
from spynnaker.pyNN.models.utility_models.delay_extension_machine_vertex \
    import DelayExtensionMachineVertex
from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)

_DELAY_PARAM_HEADER_WORDS = 7
_DEFAULT_MALLOCS_USED = 2


class DelayExtensionVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary,
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
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractProvidesNKeysForPartition.__init__(self)

        self._source_vertex = source_vertex
        self._n_delay_stages = 0
        self._delay_per_stage = delay_per_stage

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

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "machine_graph": "MemoryMachineGraph",
        "graph_mapper": "MemoryGraphMapper",
        "routing_infos": "MemoryRoutingInfos"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "machine_graph",
            "graph_mapper", "routing_infos"
        })
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            machine_graph, graph_mapper, routing_infos):

        vertex = placement.vertex

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = graph_mapper.get_slice(vertex)
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

        self.write_setup_info(spec, machine_time_step, time_scale_factor)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = routing_infos.get_first_key_from_pre_vertex(
            vertex, constants.SPIKE_PARTITION_ID)

        incoming_key = None
        incoming_mask = None
        incoming_edges = machine_graph.get_edges_ending_at_vertex(
            vertex)

        for incoming_edge in incoming_edges:
            incoming_slice = graph_mapper.get_slice(
                incoming_edge.pre_vertex)
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                r_info = routing_infos.get_routing_info_for_edge(incoming_edge)
                incoming_key = r_info.first_key
                incoming_mask = r_info.first_mask

        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask,
            self._n_vertices, machine_time_step, time_scale_factor)

        # End-of-Spec:
        spec.end_specification()

    def write_setup_info(self, spec, machine_time_step, time_scale_factor):

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(
            DelayExtensionMachineVertex._DELAY_EXTENSION_REGIONS.SYSTEM.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask,
            n_vertices, machine_time_step, time_scale_factor):
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
            (machine_time_step * time_scale_factor) /
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

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "delay_extension.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableStartType.USES_SIMULATION_INTERFACE

    def get_n_keys_for_partition(self, partition, graph_mapper):
        vertex_slice = graph_mapper.get_slice(partition.pre_vertex)
        if self._n_delay_stages == 0:
            return 1
        return vertex_slice.n_atoms * self._n_delay_stages

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [KeyAllocatorContiguousRangeContraint()]

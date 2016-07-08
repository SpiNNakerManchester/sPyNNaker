from data_specification.data_specification_generator import \
    DataSpecificationGenerator
from spynnaker.pyNN.models.utility_models.delay_block import DelayBlock
from spynnaker.pyNN.models.utility_models.delay_extension_partitioned_vertex \
    import DelayExtensionPartitionedVertex

from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_partition_constraints import \
    AbstractProvidesOutgoingPartitionConstraints
from spinn_front_end_common.utilities import constants as common_constants
from spinn_front_end_common.abstract_models\
    .abstract_provides_n_keys_for_partition \
    import AbstractProvidesNKeysForPartition
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex

from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.constraints.key_allocator_constraints\
    .key_allocator_contiguous_range_constraint \
    import KeyAllocatorContiguousRangeContraint
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

import logging
import math
import random

logger = logging.getLogger(__name__)

_DELAY_PARAM_HEADER_WORDS = 7
_DEFAULT_MALLOCS_USED = 2


class DelayExtensionVertex(
        AbstractPartitionableVertex,
        AbstractDataSpecableVertex,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractProvidesNKeysForPartition):
    """ Provide delays to incoming spikes in multiples of the maximum delays\
        of a neuron (typically 16 or 32)
    """

    _n_subvertices = 0

    def __init__(self, n_neurons, delay_per_stage, source_vertex,
                 machine_time_step, timescale_factor, constraints=None,
                 label="DelayExtension"):
        """
        Creates a new DelayExtension Object.
        """
        AbstractPartitionableVertex.__init__(
            self, n_neurons, label, 256, constraints)
        AbstractDataSpecableVertex.__init__(
            self, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)
        AbstractProvidesNKeysForPartition.__init__(self)

        self._source_vertex = source_vertex
        self._n_delay_stages = 0
        self._delay_per_stage = delay_per_stage

        # Dictionary of vertex_slice -> delay block for data specification
        self._delay_blocks = dict()

        self.add_constraint(
            PartitionerSameSizeAsVertexConstraint(source_vertex))

    def create_subvertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        DelayExtensionVertex._n_subvertices += 1
        return DelayExtensionPartitionedVertex(
            resources_required, label, constraints)

    @property
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

    def generate_data_spec(
            self, subvertex, placement, partitioned_graph, graph, routing_info,
            hostname, graph_mapper, report_folder, ip_tags, reverse_ip_tags,
            write_text_specs, application_run_time_folder):

        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder,
                write_text_specs, application_run_time_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        # ###################################################################
        # Reserve SDRAM space for memory areas:
        vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
        n_words_per_stage = int(math.ceil(vertex_slice.n_atoms / 32.0))
        delay_params_sz = \
            4 * (_DELAY_PARAM_HEADER_WORDS +
                 (self._n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=(
                DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.SYSTEM.value),
            size=common_constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4,
            label='setup')

        spec.reserve_memory_region(
            region=(
                DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value),
            size=delay_params_sz, label='delay_params')

        subvertex.reserve_provenance_data_region(spec)

        self.write_setup_info(spec)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = None
        partitions = partitioned_graph.\
            outgoing_edges_partitions_from_vertex(subvertex)
        for partition in partitions.values():
            keys_and_masks = \
                routing_info.get_keys_and_masks_from_partition(partition)

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        incoming_key = None
        incoming_mask = None
        incoming_edges = partitioned_graph.incoming_subedges_from_subvertex(
            subvertex)

        for incoming_edge in incoming_edges:
            incoming_slice = graph_mapper.get_subvertex_slice(
                incoming_edge.pre_subvertex)
            if (incoming_slice.lo_atom == vertex_slice.lo_atom and
                    incoming_slice.hi_atom == vertex_slice.hi_atom):
                partition = partitioned_graph.get_partition_of_subedge(
                    incoming_edge)
                keys_and_masks = \
                    routing_info.get_keys_and_masks_from_partition(partition)
                incoming_key = keys_and_masks[0].key
                incoming_mask = keys_and_masks[0].mask

        self.write_delay_parameters(
            spec, vertex_slice, key, incoming_key, incoming_mask,
            self._n_subvertices)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

        return data_writer.filename

    def write_setup_info(self, spec):

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(
            spec,
            (DelayExtensionPartitionedVertex.
                _DELAY_EXTENSION_REGIONS.SYSTEM.value))

    def write_delay_parameters(
            self, spec, vertex_slice, key, incoming_key, incoming_mask,
            n_subvertices):
        """ Generate Delay Parameter data
        """

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            region=(
                DelayExtensionPartitionedVertex.
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
        spec.write_value(random.randint(0, n_subvertices))

        # Write the time between spikes
        spikes_per_timestep = self._n_delay_stages * vertex_slice.n_atoms
        time_between_spikes = (
            (self._machine_time_step * self._timescale_factor) /
            (spikes_per_timestep * 2.0))
        spec.write_value(data=int(time_between_spikes))

        # Write the actual delay blocks
        spec.write_array(array_values=self._delay_blocks[(
            vertex_slice.lo_atom, vertex_slice.hi_atom)].delay_block)

    # inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        size_of_mallocs = (
            _DEFAULT_MALLOCS_USED *
            common_constants.SARK_PER_MALLOC_SDRAM_USAGE)
        return (
            size_of_mallocs +
            DelayExtensionPartitionedVertex.get_provenance_data_size(0))

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    def get_binary_file_name(self):
        return "delay_extension.aplx"

    def is_data_specable(self):
        return True

    def get_n_keys_for_partition(self, partition, graph_mapper):
        vertex_slice = graph_mapper.get_subvertex_slice(
            partition.edges[0].pre_subvertex)
        if self._n_delay_stages == 0:
            return 1
        return vertex_slice.n_atoms * self._n_delay_stages

    def get_outgoing_partition_constraints(self, partition, graph_mapper):
        return [KeyAllocatorContiguousRangeContraint()]

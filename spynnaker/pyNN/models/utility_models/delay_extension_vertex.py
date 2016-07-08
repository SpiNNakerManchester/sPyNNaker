
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

logger = logging.getLogger(__name__)


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

        return subvertex.generate_data_spec(
            subvertex, placement, partitioned_graph, graph, routing_info,
            hostname, graph_mapper, report_folder, write_text_specs,
            application_run_time_folder, DelayExtensionVertex._n_subvertices)

    # inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        size_of_mallocs = (
            DelayExtensionPartitionedVertex.DEFAULT_MALLOCS_USED *
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

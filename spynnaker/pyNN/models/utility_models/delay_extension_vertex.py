import logging
from enum import Enum
import math

from spynnaker.pyNN.utilities import constants

from spinn_front_end_common.abstract_models.\
    abstract_outgoing_edge_same_contiguous_keys_restrictor import \
    OutgoingEdgeSameContiguousKeysRestrictor
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.abstract_models\
    .abstract_provides_incoming_edge_constraints \
    import AbstractProvidesIncomingEdgeConstraints
from spynnaker.pyNN.models.utility_models.delay_block import DelayBlock
from spinn_front_end_common.abstract_models.abstract_provides_n_keys_for_edge \
    import AbstractProvidesNKeysForEdge
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex

from pacman.model.constraints.partitioner_constraints.\
    partitioner_same_size_as_vertex_constraint \
    import PartitionerSameSizeAsVertexConstraint
from pacman.model.constraints.key_allocator_constraints.\
    key_allocator_fixed_mask_constraint \
    import KeyAllocatorFixedMaskConstraint
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

from data_specification.data_specification_generator\
    import DataSpecificationGenerator


logger = logging.getLogger(__name__)

_DELAY_PARAM_HEADER_WORDS = 3


class DelayExtensionVertex(AbstractPartitionableVertex,
                           AbstractDataSpecableVertex,
                           AbstractProvidesIncomingEdgeConstraints,
                           AbstractProvidesOutgoingEdgeConstraints,
                           AbstractProvidesNKeysForEdge):
    """
    Instance of this class provide delays to incoming spikes in multiples
    of the maximum delays of a neuron (typically 16 or 32)
    """
    _DELAY_EXTENSION_REGIONS = Enum(
        value="DELAY_EXTENSION_REGIONS",
        names=[('SYSTEM', 0),
               ('DELAY_PARAMS', 1),
               ('SPIKE_HISTORY', 2)])

    def __init__(self, n_neurons, delay_per_stage, source_vertex,
                 machine_time_step, timescale_factor, constraints=None,
                 label="DelayExtension"):
        """
        Creates a new DelayExtension Object.
        """

        AbstractPartitionableVertex.__init__(self, n_atoms=n_neurons,
                                             constraints=constraints,
                                             label=label,
                                             max_atoms_per_core=256)
        AbstractDataSpecableVertex.__init__(
            self, machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractProvidesIncomingEdgeConstraints.__init__(self)
        AbstractProvidesNKeysForEdge.__init__(self)

        self._source_vertex = source_vertex
        self._n_delay_stages = 0
        self._delay_per_stage = delay_per_stage
        self._outgoing_edge_key_restrictor = \
            OutgoingEdgeSameContiguousKeysRestrictor()

        # Dictionary of vertex_slice -> delay block for data specification
        self._delay_blocks = dict()

        self.add_constraint(
            PartitionerSameSizeAsVertexConstraint(source_vertex))

    def get_incoming_edge_constraints(self, partitioned_edge, graph_mapper):
        return list([KeyAllocatorFixedMaskConstraint(0xFFFFF800)])

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
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
            self, subvertex, placement, sub_graph, graph, routing_info,
            hostname, graph_mapper, report_folder, ip_tags, reverse_ip_tags,
            write_text_specs, application_run_time_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single Delay Extension Block on one core.
        """
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
        delay_params_sz = 4 * (_DELAY_PARAM_HEADER_WORDS +
                               (self._n_delay_stages * n_words_per_stage))

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.SYSTEM.value,
            size=constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS * 4,
            label='setup')

        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        self.write_setup_info(spec, 0)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = None
        if len(sub_graph.outgoing_subedges_from_subvertex(subvertex)) > 0:
            keys_and_masks = routing_info.get_keys_and_masks_from_subedge(
                sub_graph.outgoing_subedges_from_subvertex(subvertex)[0])

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        self.write_delay_parameters(spec, vertex_slice, key)
        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def write_setup_info(self, spec, spike_history_region_sz):
        """
        """

        # Write this to the system region (to be picked up by the simulation):
        self._write_basic_setup_info(
            spec, self._DELAY_EXTENSION_REGIONS.SYSTEM.value)

    def write_delay_parameters(self, spec, vertex_slice, key):
        """
        Generate Delay Parameter data (region 2):
        """

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core:
        # Every outgoing edge from this vertex should have the same key

        spec.write_value(data=key)

        # Write the number of neurons in the block:
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=self._n_delay_stages)

        # Write the actual delay blocks
        spec.write_array(array_values=self._delay_blocks[(
            vertex_slice.lo_atom, vertex_slice.hi_atom)].delay_block)

    # inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return 128 * n_atoms

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        n_words_per_stage = int(math.ceil(vertex_slice.n_atoms / 32.0))
        return ((constants.BLOCK_INDEX_HEADER_WORDS * 4) +
                (_DELAY_PARAM_HEADER_WORDS * 4) +
                (n_words_per_stage * self._n_delay_stages * 4))

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms

    def get_binary_file_name(self):
        return "delay_extension.aplx"

    def is_data_specable(self):
        """
        helper method for isinstance
        :return:
        """
        return True

    def get_n_keys_for_partitioned_edge(self, partitioned_edge, graph_mapper):
        vertex_slice = graph_mapper.get_subvertex_slice(
            partitioned_edge.pre_subvertex)
        return vertex_slice.n_atoms * self._n_delay_stages

    def get_outgoing_edge_constraints(self, partitioned_edge, graph_mapper):
        """
        gets the constraints for edges going out of this vertex
        :param partitioned_edge: the parittioned edge that leaves this vertex
        :param graph_mapper: the graph mapper object
        :return: list of constraints
        """
        return self._outgoing_edge_key_restrictor\
            .get_outgoing_edge_constraints(partitioned_edge, graph_mapper)

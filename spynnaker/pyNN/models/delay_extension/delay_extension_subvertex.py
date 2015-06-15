"""
"""

from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from spinn_front_end_common.abstract_models.\
    abstract_data_specable_partitioned_vertex \
    import AbstractDataSpecablePartitionedVertex
from spinn_front_end_common.abstract_models\
    .abstract_outgoing_edge_same_contiguous_keys_restrictor \
    import AbstractOutgoingEdgeSameContiguousKeysRestrictor
from spinn_front_end_common.interface.has_n_machine_timesteps \
    import HasNMachineTimesteps
from spinn_front_end_common.utilities import data_spec_utilities
from spinn_front_end_common.utilities import simulation_utilities
from spinn_front_end_common.abstract_models.abstract_executable\
    import AbstractExecutable

from data_specification.data_specification_generator \
    import DataSpecificationGenerator

from spynnaker.pyNN.projections.delay_partitioned_edge \
    import DelayPartitionedEdge
from spynnaker.pyNN import exceptions

from enum import Enum
import math
import copy


class DelayExtensionSubvertex(
        AbstractDataSpecablePartitionedVertex, PartitionedVertex,
        AbstractOutgoingEdgeSameContiguousKeysRestrictor, HasNMachineTimesteps,
        AbstractExecutable):

    _DELAY_EXTENSION_REGIONS = Enum(
        value="DELAY_EXTENSION_REGIONS",
        names=[('HEADER', 0),
               ('DELAY_PARAMS', 1)])
    _DELAY_PARAMS_HEADER_WORDS = 3

    def __init__(self, resources_required, label, constraints, vertex_slice,
                 delay_extension_vertex, machine_time_step,
                 timescale_factor, n_machine_time_steps):
        AbstractDataSpecablePartitionedVertex.__init__(self)
        PartitionedVertex.__init__(self, resources_required, label,
                                   constraints=constraints)
        AbstractOutgoingEdgeSameContiguousKeysRestrictor.__init__(self)
        HasNMachineTimesteps.__init__(self, n_machine_time_steps)
        AbstractExecutable.__init__(self)
        self._vertex_slice = vertex_slice
        self._delay_extension_vertex = delay_extension_vertex
        self._machine_time_step = machine_time_step
        self._timescale_factor = timescale_factor

    def generate_data_spec(
            self, placement, graph, routing_info, ip_tags, reverse_ip_tags,
            report_folder, output_folder, write_text_specs):
        """
        """

        data_path, data_writer = data_spec_utilities.get_data_spec_data_writer(
            placement, output_folder)
        report_writer = None
        if write_text_specs:
            report_writer = data_spec_utilities.get_data_spec_report_writer(
                placement, report_folder)
        spec = DataSpecificationGenerator(data_writer, report_writer)

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")
        block_len_words = int(math.ceil(self._vertex_slice.n_atoms / 32.0))
        num_delay_blocks, delay_blocks = self._get_delay_blocks(graph)
        delay_params_sz = 4 * (self._DELAY_PARAMS_HEADER_WORDS +
                               (num_delay_blocks * block_len_words))
        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.HEADER.value,
            size=simulation_utilities.HEADER_REGION_BYTES,
            label="header"
        )
        spec.reserve_memory_region(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value,
            size=delay_params_sz, label='delay_params')

        simulation_utilities.simulation_write_header(
            spec, self._DELAY_EXTENSION_REGIONS.HEADER.value,
            "delay_extension", self._machine_time_step, self._timescale_factor,
            self.n_machine_timesteps)

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        key = None
        if len(graph.outgoing_subedges_from_subvertex(self)) > 0:
            keys_and_masks = routing_info.get_keys_and_masks_from_subedge(
                graph.outgoing_subedges_from_subvertex(self)[0])

            # NOTE: using the first key assigned as the key.  Should in future
            # get the list of keys and use one per neuron, to allow arbitrary
            # key and mask assignments
            key = keys_and_masks[0].key

        self._write_delay_parameters(spec, num_delay_blocks, delay_blocks, key)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()
        if write_text_specs:
            report_writer.close()

        return data_path

    def _get_delay_blocks(self, graph):
        """ Get the delay blocks for this vertex slice
        """

        num_words_per_row = int(math.ceil(self._vertex_slice.n_atoms / 32.0))
        one_block = [0] * num_words_per_row
        delay_block = list()
        num_delay_blocks = 0

        for subedge in graph.outgoing_subedges_from_subvertex(self):
            if not isinstance(subedge, DelayPartitionedEdge):
                raise exceptions.DelayExtensionException(
                    "One of the incoming edges is not a DelayPartitionedEdge")

            # Loop through each possible delay block
            synapse_list = subedge.edge.synapse_list.create_atom_sublist(
                subedge.presubvertex_slice, subedge.postsubvertex_slice)
            rows = synapse_list.get_rows()

            for (source_id, row) in zip(range(len(rows)), rows):
                for delay in row.delays:
                    stage = int(math.floor((delay - 1) /
                                           self.max_delay_per_neuron)) - 1
                    num_delay_blocks = max(stage + 1, num_delay_blocks)
                    if num_delay_blocks > self._max_stages:
                        raise Exception(
                            "Too many stages ({} of {}) have been"
                            " created for delay extension {}".format(
                                num_delay_blocks, self._max_stages,
                                self._label))
                    while num_delay_blocks > len(delay_block):
                        delay_block.append(copy.copy(one_block))

                    # This source neurons has synapses in the current delay
                    # range. So set the bit in the delay_block:
                    word_id = int(source_id / 32)
                    bit_id = source_id - (word_id * 32)
                    delay_block[stage][word_id] |= (1 << bit_id)

        return num_delay_blocks, delay_block

    def _write_delay_parameters(self, spec, num_delay_blocks,
                                delay_block, key):
        """ Write the parameters
        """

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for {} Neurons:\n"
                     .format(self._vertex_slice.n_atoms))

        # Set the focus to the memory region 2 (delay parameters):
        spec.switch_write_focus(
            region=self._DELAY_EXTENSION_REGIONS.DELAY_PARAMS.value)

        # Write header info to the memory region:
        # Write Key info for this core:
        # Every outgoing edge from this vertex should have the same key

        spec.write_value(data=key)

        # Write the number of neurons in the block:
        spec.write_value(data=self._vertex_slice.n_atoms)

        # Write the number of blocks of delays:
        spec.write_value(data=num_delay_blocks)

        # Write the actual delay blocks
        for i in range(0, num_delay_blocks):
            spec.write_array(array_values=delay_block[i])

    def get_binary_file_name(self):
        """
        """
        return "delay_extension.aplx"

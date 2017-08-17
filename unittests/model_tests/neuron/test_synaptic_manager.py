import unittest
import struct
from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from pacman.model.placements.placement import Placement
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
import spynnaker.pyNN.abstract_spinnaker_common as abstract_spinnaker_common
import spinn_utilities.conf_loader as conf_loader
import os


class MockSynapseIO(object):

    def get_block_n_bytes(self, max_row_length, n_rows):
        return 4


class MockMasterPopulationTable(object):

    def __init__(self, key_to_entry_map):
        self._key_to_entry_map = key_to_entry_map

    def extract_synaptic_matrix_data_location(
            self, key, master_pop_table_address, transceiver, x, y):
        return self._key_to_entry_map[key]


class MockTransceiverRawData(object):

    def __init__(self, data_to_read):
        self._data_to_read = data_to_read

    def read_memory(self, x, y, base_address, length):
        return self._data_to_read[base_address:base_address + length]


class TestSynapticManager(unittest.TestCase):

    def test_retrieve_synaptic_block(self):
        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)

        key = 0

        synaptic_manager = SynapticManager(
            synapse_type=None, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=config,
            population_table_type=MockMasterPopulationTable(
                {key: [(1, 0, False)]}),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiverRawData(bytearray(16))
        placement = Placement(None, 0, 0, 1)

        first_block, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0)
        same_block, row_len_1_2 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0)
        synaptic_manager.clear_connection_cache()
        different_block, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=1, index=0)

        # Check that the row lengths are all the same
        assert row_len_1 == row_len_1_2
        assert row_len_1 == row_len_2

        # Check that the block retrieved twice without reset is cached
        assert id(first_block) == id(same_block)

        # Check that the block after reset is not a copy
        assert id(first_block) != id(different_block)

    def test_retrieve_direct_block(self):
        default_config_paths = os.path.join(
            os.path.dirname(abstract_spinnaker_common.__file__),
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME)

        config = conf_loader.load_config(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME, default_config_paths)

        key = 0
        n_rows = 2

        direct_matrix = bytearray(struct.pack("<IIII", 1, 2, 3, 4))
        direct_matrix_1_expanded = bytearray(
            struct.pack("<IIIIIIII", 0, 1, 0, 1, 0, 1, 0, 2))
        direct_matrix_2_expanded = bytearray(
            struct.pack("<IIIIIIII", 0, 1, 0, 3, 0, 1, 0, 4))

        synaptic_manager = SynapticManager(
            synapse_type=None, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=config,
            population_table_type=MockMasterPopulationTable(
                {key: [(1, 0, True), (1, n_rows * 4, True)]}),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiverRawData(direct_matrix)
        placement = Placement(None, 0, 0, 1)

        data_1, row_len_1 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=n_rows, index=0)
        data_2, row_len_2 = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=key, n_rows=n_rows, index=1)

        # Row lengths should be 1
        assert row_len_1 == 1
        assert row_len_2 == 1

        # Check the data retrieved
        assert data_1 == direct_matrix_1_expanded
        assert data_2 == direct_matrix_2_expanded


if __name__ == "__main__":
    unittest.main()

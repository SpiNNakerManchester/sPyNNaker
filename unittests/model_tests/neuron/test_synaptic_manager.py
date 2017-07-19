import unittest
from spynnaker.pyNN.models.neuron.synaptic_manager import SynapticManager
from pacman.model.placements.placement import Placement


class MockSynapseIO(object):

    def get_block_n_bytes(self, max_row_length, n_rows):
        return 4


class MockMasterPopulationTable(object):

    def extract_synaptic_matrix_data_location(
            self, key, master_pop_table_address, transceiver, x, y):
        return [(1, 0, False)]


class MockTransceiver(object):

    def __init__(self, data_to_read):
        self._data_to_read = data_to_read
        self._index = -1

    def read_memory(self, x, y, base_address, length):
        self._index += 1
        return self._data_to_read[self._index]


class TestSynapticManager(unittest.TestCase):

    def test_retrieve_synaptic_block(self):
        synaptic_manager = SynapticManager(
            synapse_type=None, ring_buffer_sigma=5.0, spikes_per_second=100.0,
            config=None, population_table_type=MockMasterPopulationTable(),
            synapse_io=MockSynapseIO())

        transceiver = MockTransceiver([
            bytearray(4), bytearray(5)
        ])
        placement = Placement(None, 0, 0, 1)

        first_block = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=0, n_rows=1, index=0)
        same_block = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=0, n_rows=1, index=0)
        synaptic_manager.clear_connection_cache()
        different_block = synaptic_manager._retrieve_synaptic_block(
            transceiver=transceiver, placement=placement,
            master_pop_table_address=0, indirect_synapses_address=0,
            direct_synapses_address=0, key=0, n_rows=1, index=0)

        # Check that the block retrieved twice without reset is cached
        self.assertEqual(first_block, same_block)

        # Check that the block after reset is not a copy
        self.assertNotEqual(first_block, different_block)


if __name__ == "__main__":
    unittest.main()

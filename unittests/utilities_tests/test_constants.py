import unittest
import spynnaker.pyNN.utilities.constants as constants


class TestConstants(unittest.TestCase):
    def test_free_floating_constants(self):
        self.assertEqual(constants.SETUP_SIZE, 28)
        self.assertEqual(constants.NO_PARAMS, 10)
        self.assertEqual(constants.PARAMS_HEADER_SIZE, 3)
        self.assertEqual(constants.PARAMS_BASE_SIZE, 4 * (constants.PARAMS_HEADER_SIZE + constants.NO_PARAMS))
        self.assertEqual(constants.BLOCK_INDEX_HEADER_WORDS, 3)
        self.assertEqual(constants.BLOCK_INDEX_ROW_WORDS, 2)

        self.assertEqual(constants.RECORD_SPIKE_BIT, 1 << 0)
        self.assertEqual(constants.RECORD_STATE_BIT, 1 << 1)
        self.assertEqual(constants.RECORD_GSYN_BIT, 1 << 2)
        self.assertEqual(constants.RECORDING_ENTRY_BYTE_SIZE, 4)
        self.assertEqual(constants.BITS_PER_WORD, 32.0)

        self.assertEqual(constants.SYNAPSE_INDEX_BITS, 8)
        self.assertEqual(constants.MAX_NEURON_SIZE, (1 << constants.SYNAPSE_INDEX_BITS))
        self.assertEqual(constants.OUT_SPIKE_SIZE, (constants.MAX_NEURON_SIZE >> 5) )
        self.assertEqual(constants.OUT_SPIKE_BYTES, constants.OUT_SPIKE_SIZE * 4 )
        self.assertEqual(constants.V_BUFFER_SIZE_PER_TICK_PER_NEURON, 4)
        self.assertEqual(constants.GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON, 4)

        self.assertEqual(constants.INFINITE_SIMULATION, 4294967295)

        self.assertEqual(constants.SYNAPTIC_ROW_HEADER_WORDS, 2 + 1)

        self.assertEqual(constants.ROW_LEN_TABLE_ENTRIES, [0, 1, 8, 16, 32, 64, 128, 256])
        self.assertEqual(constants.ROW_LEN_TABLE_SIZE, 4 * len(constants.ROW_LEN_TABLE_ENTRIES))

        self.assertEqual(constants.X_CHIPS, 8)
        self.assertEqual(constants.Y_CHIPS, 8)
        self.assertEqual(constants.CORES_PER_CHIP, 18)
        self.assertEqual(constants.MASTER_POPULATION_ENTRIES, (constants.X_CHIPS * constants.Y_CHIPS * constants.CORES_PER_CHIP))
        self.assertEqual(constants.MASTER_POPULATION_TABLE_SIZE, 2 * constants.MASTER_POPULATION_ENTRIES )
        self.assertEqual(constants.NA_TO_PA_SCALE, 1000.0)
        self.assertEqual(constants.SDRAM_BASE_ADDR, 0x70000000)

        self.assertEqual(constants.WEIGHT_FLOAT_TO_FIXED_SCALE, 16.0)
        self.assertEqual(constants.SCALE, constants.WEIGHT_FLOAT_TO_FIXED_SCALE *constants. NA_TO_PA_SCALE)

        self.assertEqual(constants.MAX_SUPPORTED_DELAY_TICS, 16)
        self.assertEqual(constants.MAX_DELAY_BLOCKS, 8)
        self.assertEqual(constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK, 16)

        self.assertEqual(constants.APP_MONITOR_CORE_APPLICATION_ID, 0xAC0)
        self.assertEqual(constants.IF_CURRENT_EXP_CORE_APPLICATION_ID, 0xAC1)
        self.assertEqual(constants.SPIKESOURCEARRAY_CORE_APPLICATION_ID, 0xAC2)
        self.assertEqual(constants.SPIKESOURCEPOISSON_CORE_APPLICATION_ID, 0xAC3)
        self.assertEqual(constants.DELAY_EXTENSION_CORE_APPLICATION_ID, 0xAC4)
        self.assertEqual(constants.MUNICH_MOTOR_CONTROL_CORE_APPLICATION_ID, 0xAC5)
        self.assertEqual(constants.IF_CONDUCTIVE_EXP_CORE_APPLICATION_ID, 0xAC7)
        self.assertEqual(constants.IZK_CURRENT_EXP_CORE_APPLICATION_ID, 0xAC8)

    def test_edges_enum(self):
        self.assertEqual(constants.EDGES.EAST.value, 0)
        self.assertEqual(constants.EDGES.NORTH_EAST.value, 1)
        self.assertEqual(constants.EDGES.NORTH.value, 2)
        self.assertEqual(constants.EDGES.WEST.value, 3)
        self.assertEqual(constants.EDGES.SOUTH_WEST.value, 4)
        self.assertEqual(constants.EDGES.SOUTH.value, 5)

    def test_population_based_regions_enum(self):
        self.assertEqual(constants.POPULATION_BASED_REGIONS.SYSTEM.value, 0)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value, 1)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value, 2)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.ROW_LEN_TRANSLATION.value, 3)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value, 4)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value, 5)

        self.assertEqual(constants.POPULATION_BASED_REGIONS.STDP_PARAMS.value, 6)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value, 7)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value, 8)
        self.assertEqual(constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value, 9)

if __name__ == '__main__':
    unittest.main()

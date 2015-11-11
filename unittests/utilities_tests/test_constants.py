import unittest
import spynnaker.pyNN.utilities.constants as constants


class TestConstants(unittest.TestCase):
    def test_free_floating_constants(self):
        self.assertEqual(constants.DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS, 3)
        self.assertEqual(constants.BLOCK_INDEX_HEADER_WORDS, 3)
        self.assertEqual(constants.BLOCK_INDEX_ROW_WORDS, 2)

        self.assertEqual(constants.RECORD_SPIKE_BIT, 1 << 0)
        self.assertEqual(constants.RECORD_STATE_BIT, 1 << 1)
        self.assertEqual(constants.RECORD_GSYN_BIT, 1 << 2)
        self.assertEqual(constants.RECORDING_ENTRY_BYTE_SIZE, 4)

        self.assertEqual(constants.SYNAPSE_INDEX_BITS, 8)
        self.assertEqual(
            constants.MAX_NEURON_SIZE, (1 << constants.SYNAPSE_INDEX_BITS))
        self.assertEqual(
            constants.OUT_SPIKE_SIZE, (constants.MAX_NEURON_SIZE >> 5))
        self.assertEqual(
            constants.OUT_SPIKE_BYTES, constants.OUT_SPIKE_SIZE * 4)
        self.assertEqual(constants.V_BUFFER_SIZE_PER_TICK_PER_NEURON, 4)
        self.assertEqual(constants.GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON, 4)

        self.assertEqual(constants.INFINITE_SIMULATION, 4294967295)

        self.assertEqual(constants.SYNAPTIC_ROW_HEADER_WORDS, 2 + 1)

        self.assertEqual(constants.NA_TO_PA_SCALE, 1000.0)

        self.assertEqual(constants.WEIGHT_FLOAT_TO_FIXED_SCALE, 16.0)
        self.assertEqual(
            constants.SCALE, constants.WEIGHT_FLOAT_TO_FIXED_SCALE *
            constants. NA_TO_PA_SCALE)

        self.assertEqual(constants.MAX_SUPPORTED_DELAY_TICS, 16)
        self.assertEqual(constants.MAX_DELAY_BLOCKS, 8)
        self.assertEqual(constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK, 16)

    def test_population_based_regions_enum(self):
        self.assertEqual(constants.POPULATION_BASED_REGIONS.SYSTEM.value, 0)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.NEURON_PARAMS.value, 1)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.SYNAPSE_PARAMS.value, 2)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.ROW_LEN_TRANSLATION.value, 3)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value, 4)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value, 5)

        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.STDP_PARAMS.value, 6)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value, 7)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value, 8)
        self.assertEqual(
            constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value, 9)

if __name__ == '__main__':
    unittest.main()

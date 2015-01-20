import unittest

from spynnaker.pyNN.models.utility_models.live_packet_gather \
    import LivePacketGather
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint


class TestLiveSpikeRecorder(unittest.TestCase):
    def test_new_live_spike_recorder(self):
        live_spike_recorder = LivePacketGather(1000, 1, 1, 1, "")
        constraint_list_copy = list()
        constraint_list_copy.extend(live_spike_recorder.constraints)
        for index in range(len(constraint_list_copy)):
            constraint_list_copy[index] = type(constraint_list_copy[index])
        self.assertIn(type(PlacerChipAndCoreConstraint(0, 0)),
                      constraint_list_copy)
        for index in range(len(constraint_list_copy)):
            if constraint_list_copy[index] is PlacerChipAndCoreConstraint:
                self.assertEqual(live_spike_recorder.constraints[index].x, 0)
                self.assertEqual(live_spike_recorder.constraints[index].y, 0)

    @unittest.skip("Not implemented")
    def test_generate_data_spec(self):
        self.assertEqual(True, "Test not implemented yet")

    @unittest.skip("Not implemented")
    def test_reserer_memory_regions(self):
        self.assertEqual(True, "Test not implemented yet")

    @unittest.skip("Not implemented")
    def test_write_setup_info(self):
        self.assertEqual(True, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()

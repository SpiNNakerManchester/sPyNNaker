
import unittest

from spinn_front_end_common.utility_models import LivePacketGather


class TestLiveSpikeRecorder(unittest.TestCase):

    def test_new_live_spike_recorder(self):
        LivePacketGather(1000, 1, 1, 1, "")


if __name__ == '__main__':
    unittest.main()

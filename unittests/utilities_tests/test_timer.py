import unittest

from spinn_front_end_common.utilities.timer import Timer
from time import sleep


class TestTimer(unittest.TestCase):
    def test_timer(self):
        timer = Timer()
        timer.start_timing()
        sleep(2)
        self.assertEqual(timer.take_sample().seconds,2)
        sleep(1)
        self.assertEqual(timer.take_sample().seconds,3)


if __name__ == '__main__':
    unittest.main()

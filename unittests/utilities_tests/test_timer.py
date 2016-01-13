import unittest
from time import sleep

from pacman.utilities.utility_objs.timer import Timer


class TestTimer(unittest.TestCase):
    def test_timer(self):
        timer = Timer()
        timer.start_timing()
        sleep(0.1)
        end_time = timer.take_sample().total_seconds()
        self.assertAlmostEqual(end_time, 0.1, delta=0.02)
        sleep(0.2)
        self.assertAlmostEqual(timer.take_sample().total_seconds(),
                               end_time + 0.2, delta=0.02)


if __name__ == '__main__':
    unittest.main()

import unittest
from spinn_front_end_common.utilities.exceptions import ConfigurationException
import spynnaker.pyNN as p


class TestgetMinDelay(unittest.TestCase):

    def test_get_min_delay_0_1_milisecond_timestep(self):
        """
        tests if with no user min, the min is set to 1 timestep in millisencsd
        :return:
        """
        p.setup(0.1)
        min_delay = p.get_min_delay()
        self.assertEqual(min_delay, 0.1)

    def test_get_min_delay_1_millisecond_timestep(self):
        """
         tests if with no user min, the min is set to 1 timestep in milli
        :return:
        """
        p.setup(1)
        min_delay = p.get_min_delay()
        self.assertEqual(min_delay, 1)

    def test_invalid_min_delay_1_millisecond_timestep(self):
        """
         tests if with invalid user min, the min raises exefpetiosn
        :return:
        """
        with self.assertRaises(ConfigurationException):
            p.setup(1, min_delay=0.1)

    def test_valid_min_delay_1_millisecond_timestep(self):
        """
        tests if with valid user min, the min is set correctly
        :return:
        """
        p.setup(1, min_delay=4)
        min_delay = p.get_min_delay()
        self.assertEqual(min_delay, 4)

    def test_valid_min_delay_0_1_millisecond_timestep(self):
        """
        tests if with valid user min, the min is set correctly
        :return:
        """
        p.setup(0.1, min_delay=4)
        min_delay = p.get_min_delay()
        self.assertEqual(min_delay, 4)

    def test_valid_min_delay_0_1_millisecond_timestep_take_2(self):
        """
        tests if with valid user min, the min is set correctly
        :return:
        """
        p.setup(0.1, min_delay=0.4)
        min_delay = p.get_min_delay()
        self.assertEqual(min_delay, 0.4)

    def test_valid_max_delay_0_1_millisecond_timestep(self):
        """
        tests if with valid user min, the min is set correctly
        :return:
        """
        p.setup(0.1, max_delay=0.4)
        max_delay = p.get_max_delay()
        self.assertEqual(max_delay, 0.4)

    def test_max_delay_no_user_input_0_1_millisecond_timestep(self):
        """
        Tests that with no user input, the max delay is correct
        :return:
        """
        p.setup(0.1)
        max_delay = p.get_max_delay()
        self.assertEqual(max_delay, 14.4)

    def test_max_delay_no_user_input_1_millisecond_timestep(self):
        """
        Tests that with no user input, the max delay is correct
        :return:
        """
        p.setup(1)
        max_delay = p.get_max_delay()
        self.assertEqual(max_delay, 144)

    def test_invalid_max_delay(self):
        """
        tests that with invalid user input the max delay raises correctly
        :return:
        """
        with self.assertRaises(ConfigurationException):
            p.setup(1, max_delay=100000)


if __name__ == '__main__':
    unittest.main()

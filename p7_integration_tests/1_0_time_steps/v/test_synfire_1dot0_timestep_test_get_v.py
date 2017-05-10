"""
Synfirechain-like example
"""
# spynnaker imports
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun
import spynnaker.pyNN.utilities.utility_calls as utility_calls

# general imports
import os
import unittest

n_neurons = 200  # number of neurons in each population
runtime = 500
max_delay = 14.4
timestep = 1
neurons_per_core = n_neurons/2
delay = 1.7
synfire_run = TestRun()


class TestGetVoltage(BaseTestCase):
    """
    tests the printing of get v given a simulation
    """

    def test_get_voltage(self):
        """
        test that tests the getting of v from a pre determined recording
        :return:
        """
        synfire_run.do_run(n_neurons, max_delay=max_delay, time_step=timestep,
                           neurons_per_core=neurons_per_core, delay=delay,
                           run_times=[runtime])
        v = synfire_run.get_output_pop_voltage()

        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_file_path = os.path.join(current_file_path, "v.data")
        pre_recorded_data = utility_calls.read_in_data_from_file(
            current_file_path, 0, n_neurons, 0, runtime)

        for v_element, read_element in zip(v, pre_recorded_data):
            self.assertAlmostEqual(v_element[0], read_element[0], delta=0.1)
            self.assertAlmostEqual(v_element[1], read_element[1], delta=0.1)
            self.assertAlmostEqual(v_element[2], read_element[2], delta=1)


if __name__ == '__main__':
    unittest.main()

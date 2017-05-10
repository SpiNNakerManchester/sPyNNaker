"""
Synfirechain-like example
"""
import os
import unittest
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun
import spynnaker.pyNN.utilities.utility_calls as utility_calls
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest

n_neurons = 20
timestep = 0.1
max_delay = 14.40
delay = 1.7
neurons_per_core = n_neurons/2
runtime = 500
current_file_path = os.path.dirname(os.path.abspath(__file__))
current_file_path = os.path.join(current_file_path, "spikes.data")
synfire_run = TestRun()


class TestPrintSpikes(BaseTestCase):
    """
    tests the printing of get spikes given a simulation
    """

    def test_print_spikes(self):
        try:
            synfire_run.do_run(n_neurons, time_step=timestep,
                               max_delay=max_delay, delay=delay,
                               neurons_per_core=neurons_per_core,
                               run_times=[runtime],
                               spike_path=current_file_path)
            spikes = synfire_run.get_output_pop_spikes()

            read_in_spikes = utility_calls.read_spikes_from_file(
                current_file_path, min_atom=0, max_atom=n_neurons,
                min_time=0, max_time=500)

            for spike_element, read_element in zip(spikes, read_in_spikes):
                self.assertEqual(round(spike_element[0], 1),
                                 round(read_element[0], 1))
                self.assertEqual(round(spike_element[1], 1),
                                 round(read_element[1], 1))
        except SpinnmanTimeoutException as ex:
            # System intentional overload so may error
            raise SkipTest(ex)


if __name__ == '__main__':
    unittest.main()

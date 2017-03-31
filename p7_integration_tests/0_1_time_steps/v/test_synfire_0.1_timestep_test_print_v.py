"""
Synfirechain-like example
"""
# general imports
import os
import unittest
import p7_integration_tests.scripts.synfire_run as synfire_run
import spynnaker.pyNN.utilities.utility_calls as utility_calls


class TestPrintVoltage(unittest.TestCase):
    """
    tests the printing of print v given a simulation
    """

    def test_print_voltage(self):
        """
        test that tests the printing of v from a pre determined recording
        :return:
        """
        n_neurons = 200  # number of neurons in each population
        runtime = 500
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_v_file_path = os.path.join(current_file_path, "v.data2")
        results = synfire_run.do_run(n_neurons, max_delay=14, timestep=0.1,
                                     neurons_per_core=10, delay=1.7,
                                     runtimes=[runtime],
                                     v_path=current_v_file_path)
        (v, gsyn, spikes) = results
        read_in_v_values = utility_calls.read_in_data_from_file(
            current_v_file_path, 0, n_neurons, 0, runtime)

        for v_element, read_element in zip(v, read_in_v_values):
            self.assertEqual(round(v_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(v_element[1], 1),
                             round(read_element[1], 1))
            self.assertEqual(round(v_element[2], 1),
                             round(read_element[2], 1))
        os.remove(current_v_file_path)


if __name__ == '__main__':
    unittest.main()

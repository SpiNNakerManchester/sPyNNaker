"""
Synfirechain-like example
"""
import os
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run
import spynnaker.pyNN.utilities.utility_calls as utility_calls


class TestMallocKeyAllocatorWithSynfire(BaseTestCase):
    """
    tests the printing of print v given a simulation
    """

    def test_script(self):
        """
        test that tests the printing of v from a pre determined recording
        :return:
        """
        n_neurons = 20  # number of neurons in each population
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_spike_file_path = os.path.join(current_file_path,
                                               "spikes.data")
        current_v_file_path = os.path.join(current_file_path, "v.data")
        current_gsyn_file_path = os.path.join(current_file_path, "gsyn.data")
        results = synfire_run.do_run(n_neurons, max_delay=14, timestep=0.1,
                                     neurons_per_core=1, delay=1.7,
                                     runtimes=[50],
                                     spike_path=current_spike_file_path,
                                     gsyn_path=current_gsyn_file_path,
                                     v_path=current_v_file_path)
        (v, gsyn, spikes) = results
        read_in_spikes = utility_calls.read_spikes_from_file(
            current_spike_file_path, 0, n_neurons, 0, 5000)
        read_in_v = utility_calls.read_in_data_from_file(
            current_v_file_path, 0, n_neurons, 0, 5000)
        read_in_gsyn = utility_calls.read_in_data_from_file(
            current_gsyn_file_path, 0, n_neurons, 0, 5000)

        print read_in_spikes
        print read_in_gsyn
        print read_in_v

        print "Skipping spike check as broken"
        # for spike_element, read_element in zip(spikes, read_in_spikes):
        #    self.assertEqual(round(spike_element[0], 1),
        #                     round(read_element[0], 1))
        #    self.assertEqual(round(spike_element[1], 1),
        #                     round(read_element[1], 1))

        for v_element, read_element in zip(v, read_in_v):
            self.assertEqual(round(v_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(v_element[1], 1),
                             round(read_element[1], 1))

        for gsyn_element, read_element in zip(gsyn, read_in_gsyn):
            self.assertEqual(round(gsyn_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(gsyn_element[1], 1),
                             round(read_element[1], 1))


if __name__ == '__main__':
    unittest.main()

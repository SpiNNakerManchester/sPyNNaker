"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run

n_neurons = 200
timestep = 0.1
max_delay = 14.40
delay = 1.7
neurons_per_core = n_neurons/2
runtime = 500


class TestGetSpikesAt0_1msTimeStep(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    def test_get_spikes(self):
        """
        test for get spikes
        """

        results = synfire_run.do_run(n_neurons, timestep=timestep,
                                     max_delay=max_delay, delay=delay,
                                     neurons_per_core=neurons_per_core,
                                     runtimes=[runtime])
        (v, gsyn, spikes) = results

        pre_recorded_spikes = [
            [0, 3.5], [1, 6.6], [2, 9.7], [3, 12.8], [4, 15.9], [5, 19.],
            [6, 22.1], [7, 25.2], [8, 28.3], [9, 31.4], [10, 34.5], [11, 37.6],
            [12, 40.7], [13, 43.8], [14, 46.9], [15, 50.], [16, 53.1],
            [17, 56.2], [18, 59.3], [19, 62.4], [20, 65.5], [21, 68.6],
            [22, 71.7], [23, 74.8], [24, 77.9], [25, 81.0], [26, 84.1],
            [27, 87.2], [28, 90.3], [29, 93.4], [30, 96.5], [31, 99.6],
            [32, 102.7], [33, 105.8], [34, 108.8], [35, 111.9], [36, 115.],
            [37, 118.1], [38, 121.2], [39, 124.3], [40, 127.4], [41, 130.5],
            [42, 133.6], [43, 136.7], [44, 139.8], [45, 142.9], [46, 146.],
            [47, 149.1], [48, 152.2], [49, 155.3], [50, 158.4], [51, 161.5],
            [52, 164.6], [53, 167.7]]

        for spike_element, read_element in zip(spikes, pre_recorded_spikes):
            self.assertEqual(spike_element[0], read_element[0])
            self.assertAlmostEqual(spike_element[1], read_element[1],
                                   delta=0.4)


if __name__ == '__main__':
    unittest.main()

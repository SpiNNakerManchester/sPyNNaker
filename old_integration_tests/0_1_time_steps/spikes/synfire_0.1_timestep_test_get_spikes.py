"""
Synfirechain-like example
"""
#import pyNN.spiNNaker as p
import spynnaker.pyNN as p
import unittest

cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0}


class TestGetSpikesAt0_1msTimeStep(unittest.TestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    def test_get_spikes(self):
        """
        test for get spikes
        :return:
        """
        p.setup(timestep=0.1, min_delay=1.0, max_delay=14.40)
        n_neurons = 200  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()

        weight_to_spike = 2.0
        delay = 1.7

        loop_connections = list()
        for i in range(0, n_neurons):
            single_connection = (i, ((i + 1) % n_neurons), weight_to_spike,
                                 delay)
            loop_connections.append(single_connection)

        injection_connection = [(0, 0, weight_to_spike, 1)]
        spike_array = {'spike_times': [[0]]}
        populations.append(p.Population(
            n_neurons, p.IF_curr_exp, cell_params_lif, label='pop_1'))
        populations.append(p.Population(
            1, p.SpikeSourceArray, spike_array, label='inputSpikes_1'))

        projections.append(p.Projection(populations[0], populations[0],
                           p.FromListConnector(loop_connections)))
        projections.append(p.Projection(populations[1], populations[0],
                           p.FromListConnector(injection_connection)))

        populations[0].record_v()
        populations[0].record_gsyn()
        populations[0].record()

        p.run(500)

        spikes = populations[0].getSpikes(compatible_output=True)
        pre_recorded_spikes = [
            [0, 3.5], [1, 6.7], [2, 9.9], [3, 13.1], [4, 16.3],
            [5, 19.5], [6, 22.7], [7, 25.9], [8, 29.1],
            [9, 32.3], [10, 35.5], [11, 38.7], [12, 41.9],
            [13, 45.1], [14, 48.3], [15, 51.5], [16, 54.7],
            [17, 57.9], [18, 61.1], [19, 64.3], [20, 67.5],
            [21, 70.7], [22, 73.9], [23, 77.1], [24, 80.3],
            [25, 83.5], [26, 86.7], [27, 89.9], [28, 93.1],
            [29, 96.3], [30, 99.5], [31, 102.7], [32, 105.9],
            [33, 109.1], [34, 112.3], [35, 115.5], [36, 118.7],
            [37, 121.9], [38, 125.1], [39, 128.3], [40, 131.5],
            [41, 134.7], [42, 137.9], [43, 141.1], [44, 144.3],
            [45, 147.5], [46, 150.7], [47, 153.9], [48, 157.1],
            [49, 160.3], [50, 163.5], [51, 166.7], [52, 169.9],
            [53, 173.1], [54, 176.3], [55, 179.5], [56, 182.7],
            [57, 185.9], [58, 189.1], [59, 192.3], [60, 195.5]]

        p.end()

        for spike_element, read_element in zip(spikes, pre_recorded_spikes):
            self.assertEqual(round(spike_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(spike_element[1], 1),
                             round(read_element[1], 1))

if __name__ == '__main__':
    unittest.main()

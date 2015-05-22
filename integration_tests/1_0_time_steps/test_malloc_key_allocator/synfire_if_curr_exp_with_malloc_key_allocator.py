"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
import unittest
import os

class TestMallocKeyAllocatorWithSynfire(unittest.TestCase):
    """
    tests the printing of print v given a simulation
    """

    def test_script(self):
        """
        test that tests the printing of v from a pre determined recording
        :return:
        """
        p.setup(timestep=1, min_delay=1.0, max_delay=14)
        n_neurons = 20  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", 1)

        cell_params_lif = {'cm': 0.25,
                           'i_offset': 0.0,
                           'tau_m': 20.0,
                           'tau_refrac': 2.0,
                           'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0,
                           'v_reset': -70.0,
                           'v_rest': -65.0,
                           'v_thresh': -50.0
                           }

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
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif,
                           label='pop_1'))
        populations.append(p.Population(1, p.SpikeSourceArray, spike_array,
                           label='inputSpikes_1'))

        projections.append(p.Projection(populations[0], populations[0],
                           p.FromListConnector(loop_connections)))
        projections.append(p.Projection(populations[1], populations[0],
                           p.FromListConnector(injection_connection)))

        populations[0].record_v()
        populations[0].record_gsyn()
        populations[0].record()

        p.run(50)

        v = populations[0].get_v(compatible_output=True)
        gsyn = populations[0].get_gsyn(compatible_output=True)
        spikes = populations[0].getSpikes(compatible_output=True)
        print spikes
        print gsyn
        print v

        # end sim
        p.end()

        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_spike_file_path = os.path.join(current_file_path, "spikes.data")
        current_v_file_path = os.path.join(current_file_path, "v.data")
        current_gsyn_file_path = os.path.join(current_file_path, "gsyn.data")

        populations[0].print_v(current_v_file_path)
        populations[0].print_gsyn(current_gsyn_file_path)
        populations[0].printSpikes(current_spike_file_path)

        read_in_spikes = p.utility_calls.read_spikes_from_file(
            current_spike_file_path, 0, n_neurons, 0, 5000)
        read_in_v = p.utility_calls.read_in_data_from_file(
            current_v_file_path, 0, n_neurons, 0, 5000)
        read_in_gsyn = p.utility_calls.read_in_data_from_file(
            current_gsyn_file_path, 0, n_neurons, 0, 5000)

        print read_in_spikes
        print read_in_gsyn
        print read_in_v

        for spike_element, read_element in zip(spikes, read_in_spikes):
            self.assertEqual(round(spike_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(spike_element[1], 1),
                             round(read_element[1], 1))

        for v_element, read_element in zip(v, read_in_v):
            self.assertEqual(round(spike_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(spike_element[1], 1),
                             round(read_element[1], 1))

        for gsyn_element, read_element in zip(gsyn, read_in_gsyn):
            self.assertEqual(round(spike_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(spike_element[1], 1),
                             round(read_element[1], 1))

if __name__ == '__main__':
    unittest.main()

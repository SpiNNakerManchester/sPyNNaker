"""
Synfirechain-like example
"""

# spynnaker imports
import spynnaker.pyNN as p

# general imports
import os
import unittest

class TestPrintGsyn(unittest.TestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_print_gsyn(self):
        """
        test that tests the printing of gsyn
        :return:
        """

        p.setup(timestep=0.1, min_delay=1.0, max_delay=14.40)
        n_neurons = 200  # number of neurons in each population
        runtime = 500
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

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

        p.run(runtime)

        gsyn = populations[0].get_gsyn(compatible_output=True)

        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_file_path = os.path.join(current_file_path, "gsyn.data2")
        populations[0].print_gsyn(current_file_path)

        read_in_gsyn_values = \
            p.utility_calls.read_in_data_from_file(
                current_file_path, 0, n_neurons, 0, runtime)

        os.remove(current_file_path)
        p.end()

        for spike_element, read_element in zip(gsyn, read_in_gsyn_values):
            self.assertEqual(round(spike_element[0], 1),
                             round(read_element[0], 1))
            self.assertEqual(round(spike_element[1], 1),
                             round(read_element[1], 1))
            self.assertEqual(round(spike_element[2], 1),
                             round(read_element[2], 1))

if __name__ == '__main__':
    unittest.main()

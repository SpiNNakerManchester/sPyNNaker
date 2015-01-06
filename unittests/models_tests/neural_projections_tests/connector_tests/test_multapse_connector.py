#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pyNN
from pprint import pprint as pp
cell_params_lif = {
    'cm': 0.25,
    'i_offset': 0.0,
    'tau_m': 20.0,
    'tau_refrac': 2.0,
    'tau_syn_E': 5.0,
    'tau_syn_I': 5.0,
    'v_reset': -70.0,
    'v_rest': -65.0,
    'v_thresh': -50.0
}
if pyNN._spinnaker is None:
    pyNN.setup(timestep=1, min_delay=1, max_delay=10)


class MultapseConnectorTest(unittest.TestCase):
    def test_a(self):
        weight = 2
        delay = 1
        first_pop = pyNN.Population(5, pyNN.IF_curr_exp, cell_params_lif,
                                    label="First normal pop")
        second_pop = pyNN.Population(10, pyNN.IF_curr_exp, cell_params_lif,
                                     label="Second normal pop")
        pyNN.Projection(first_pop, second_pop, pyNN.MultapseConnector(
            num_synapses=5, weights=weight, delays=delay))

    def test_nasty(self):
        weight = 2
        delay = 1
        first_pop = pyNN.Population(5, pyNN.IF_curr_exp, cell_params_lif,
                                    label="First normal pop")
        pyNN.Projection(first_pop, first_pop, pyNN.MultapseConnector(
            num_synapses=10, weights=weight, delays=delay))

    def test_generate_synaptic_list(self):
        number_of_neurons = 5
        first_population = pyNN.Population(number_of_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="One pop")
        weight = 2
        delay = 1
        synapse_type = first_population._vertex.get_synapse_id('excitatory')
        connection = pyNN.MultapseConnector(1, weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, first_population, 1, 1.0, synapse_type)
        pp(synaptic_list.get_rows())


if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pyNN
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from pprint import pprint as pp

nNeurons = 10
cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0}
spike_array = {'spike_times': [0]}


class TestingOneToOneConnector(unittest.TestCase):
    def setUp(self):
        pyNN.setup(timestep=1, min_delay=1, max_delay=10.0)

    def tearDown(self):
        pyNN.end()

    @unittest.skip("broken; API changed")
    def test_connect_two_different_populations(self):
        number_of_neurons = 10
        first_population = pyNN.Population(
            number_of_neurons, pyNN.IF_curr_exp, cell_params_lif,
            label="One pop")
        second_population = pyNN.Population(
            number_of_neurons, pyNN.IF_curr_exp, cell_params_lif,
            label="Second pop")
        weight = 2
        delay = 1
        synapse_type = 0
        connection = pyNN.OneToOneConnector(weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, second_population, 1, 1.0, synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(), weight)
        self.assertEqual(synaptic_list.get_min_weight(), weight)
        pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(), number_of_neurons)
        self.assertEqual(synaptic_list.get_max_delay(), delay)
        self.assertEqual(synaptic_list.get_min_delay(), delay)

    @unittest.skip("broken; API changed")
    def test_self_connect_population(self):
        number_of_neurons = 10
        first_population = pyNN.Population(
            number_of_neurons, pyNN.IF_curr_exp, cell_params_lif,
            label="One pop")
        weight = 2
        delay = 1
        synapse_type = 0
        connection = pyNN.OneToOneConnector(weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, first_population, 1, 1.0, synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(), weight)
        self.assertEqual(synaptic_list.get_min_weight(), weight)
        pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(), number_of_neurons)
        self.assertEqual(synaptic_list.get_max_delay(), delay)
        self.assertEqual(synaptic_list.get_min_delay(), delay)

    @unittest.skip("broken; API changed")
    def test_synapse_list_generation_for_different_sized_populations(self):
        number_of_neurons = 10
        first_population = pyNN.Population(
            number_of_neurons, pyNN.IF_curr_exp, cell_params_lif,
            label="One pop")
        second_population = pyNN.Population(
            number_of_neurons + 5, pyNN.IF_curr_exp, cell_params_lif,
            label="Second pop")
        weight = 2
        delay = 1
        connection = pyNN.OneToOneConnector(weight, delay)
        with self.assertRaises(ConfigurationException):
            connection.generate_synapse_list(first_population,
                                             second_population, 1, 1.0, 0)

    def test_connector_populations_of_different_sizes(self):
        weight = 2
        delay = 5
        p1 = pyNN.Population(
            10, pyNN.IF_curr_exp, cell_params_lif, label="pop 1")
        p2 = pyNN.Population(
            5, pyNN.IF_curr_exp, cell_params_lif, label="pop 2")
        j = pyNN.Projection(p1, p2, pyNN.OneToOneConnector(weight, delay))
        self.assertIsNotNone(j)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pyNN
from pprint import pprint as pp
from spinn_front_end_common.utilities.exceptions import ConfigurationException

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
# /Setup


class TestingFixedProbabilityConnector(unittest.TestCase):
    def setUp(self):
        pyNN.setup(timestep=1, min_delay=1, max_delay=10.0)

    def tearDown(self):
        pyNN.end()

    @unittest.skip("broken; API changed")
    def test_generate_synapse_list(self):
        number_of_neurons = 5
        first_population = pyNN.Population(number_of_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="One pop")
        weight = 2
        delay = 1
        synapse_type = 0
        connection = pyNN.FixedProbabilityConnector(0.5, weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, first_population, 1, 1.0, synapse_type)
        pp(synaptic_list.get_rows())

    @unittest.skip("broken; API changed")
    def test_generate_synapse_list_probability_zero_percent(self):
        number_of_neurons = 5
        first_population = pyNN.Population(number_of_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="One pop")
        weight = 2
        delay = 1
        synapse_type = 0
        connection = pyNN.FixedProbabilityConnector(0, weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, first_population, 1, 1.0, synapse_type)
        pp(synaptic_list.get_rows())

    @unittest.skip("broken; API changed")
    def test_generate_synapse_list_probability_100_percent(self):
        number_of_neurons = 5
        first_population = pyNN.Population(number_of_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="One pop")
        weight = 2
        delay = 1
        synapse_type = 0
        connection = pyNN.FixedProbabilityConnector(1, weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, first_population, 1, 1.0, synapse_type)
        pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_max_weight(), weight)
        self.assertEqual(synaptic_list.get_min_weight(), weight)
        self.assertEqual(synaptic_list.get_n_rows(), number_of_neurons)
        self.assertEqual(synaptic_list.get_max_delay(), delay)
        self.assertEqual(synaptic_list.get_min_delay(), delay)

    def test_generate_synapse_list_probability_200_percent(self):
        with self.assertRaises(ConfigurationException):
            weight = 2
            delay = 1
            pyNN.FixedProbabilityConnector(2, weight, delay)

    def test_synapse_list_generation_for_negative_sized_populations(self):
        with self.assertRaises(ConfigurationException):
            weight = 2
            delay = 1
            pyNN.FixedProbabilityConnector(-0.5, weight, delay)

    @unittest.skip("broken; API changed")
    def test_synapse_list_generation_for_different_sized_populations(self):
        number_of_neurons = 10
        first_population = pyNN.Population(number_of_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="One pop")
        second_population = pyNN.Population(number_of_neurons + 5,
                                            pyNN.IF_curr_exp, cell_params_lif,
                                            label="Second pop")
        weight = 2
        delay = 1
        connection = pyNN.FixedProbabilityConnector(0.1, weight, delay)
        synaptic_list = connection.generate_synapse_list(
            first_population, second_population, 1, 1.0, 0)
        pp(synaptic_list.get_rows())

    @unittest.skip("broken; API changed")
    def test_allow_self_connections(self):
        number_of_neurons = 5
        first_population = pyNN.Population(number_of_neurons, pyNN.IF_curr_exp,
                                           cell_params_lif, label="One pop")
        weight = 2
        delay = 1
        synapse_type = 0
        connection = pyNN.FixedProbabilityConnector(
            1, weight, delay, allow_self_connections=False)
        synaptic_list = connection.generate_synapse_list(
            first_population, first_population, 1, 1.0, synapse_type)
        pp(synaptic_list.get_rows())


if __name__ == "__main__":
    unittest.main()

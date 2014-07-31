#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pynn
from pprint import pprint as pp
from spynnaker.pyNN.exceptions import ConfigurationException
#Setup
pynn.setup(timestep=1, min_delay=1, max_delay=10.0)

cell_params_lif = {'cm'  : 0.25,
             'i_offset'  : 0.0,
             'tau_m'     : 20.0,
             'tau_refrac': 2.0,
             'tau_syn_E' : 5.0,
             'tau_syn_I' : 5.0,
             'v_reset'   : -70.0,
             'v_rest'    : -65.0,
             'v_thresh'  : -50.0
             }
spike_array = {'spike_times':[0]}
#/Setup

class TestingFixedNumberPreConnector(unittest.TestCase):
    def test_generate_synapse_list_pre_0(self):
        number_of_neurons = 5
        first_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        second_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = first_population._vertex.get_synapse_id('excitatory')
        connection = pynn.FixedNumberPreConnector(0,weight,delay)
        synaptic_list = connection.generate_synapse_list(first_population._vertex,first_population._vertex,1,synapse_type)
        pp(synaptic_list.get_rows())

    def test_generate_synapse_list_pre_1(self):
        number_of_neurons = 5
        first_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        second_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = first_population._vertex.get_synapse_id('excitatory')
        connection = pynn.FixedNumberPreConnector(1,weight,delay)
        synaptic_list = connection.generate_synapse_list(first_population._vertex,first_population._vertex,1,synapse_type)
        pp(synaptic_list.get_rows())


    def test_generate_synapse_list_pre_5(self):
        number_of_neurons = 5
        first_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        second_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = first_population._vertex.get_synapse_id('excitatory')
        connection = pynn.FixedNumberPreConnector(5,weight,delay)
        synaptic_list = connection.generate_synapse_list(first_population._vertex,first_population._vertex,1,synapse_type)
        pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))


    def test_generate_synapse_list_pre_6(self):
        with self.assertRaises(ConfigurationException):
            number_of_neurons = 5
            first_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
            second_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
            weight = 2
            delay = 1
            synapse_type = first_population._vertex.get_synapse_id('excitatory')
            connection = pynn.FixedNumberPreConnector(6,weight,delay)
            synaptic_list = connection.generate_synapse_list(first_population._vertex,first_population._vertex,1,synapse_type)

    def test_generate_synapse_list_pre_negative(self):
        with self.assertRaises(ConfigurationException):
            number_of_neurons = 5
            first_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
            second_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
            weight = 2
            delay = 1
            synapse_type = first_population._vertex.get_synapse_id('excitatory')
            connection = pynn.FixedNumberPreConnector(-1,weight,delay)
            synaptic_list = connection.generate_synapse_list(first_population._vertex,first_population._vertex,1,synapse_type)

    def test_allow_self_connections(self):
        number_of_neurons = 5
        first_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        second_population=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = first_population._vertex.get_synapse_id('excitatory')
        connection = pynn.FixedNumberPreConnector(5,weight,delay,allow_self_connections = False)
        synaptic_list = connection.generate_synapse_list(first_population._vertex,first_population._vertex,1,synapse_type)
        pp(synaptic_list.get_rows())



if __name__=="__main__":
    unittest.main()
#!/usr/bin/env python
import unittest
import pacman103
import pacman103.front.pynn as pynn
import pacman103.front.pynn.connectors as connectors
from pprint import pprint as pp
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
        print "-----------------0 PRE--------------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FixedNumberPreConnector(0,weight,delay)
        #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        pp(synaptic_list.get_rows())

    def test_generate_synapse_list_pre_1(self):
        print "-----------------1 PRE--------------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FixedNumberPreConnector(1,weight,delay)
        #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        pp(synaptic_list.get_rows())


    def test_generate_synapse_list_pre_5(self):
        print "-----------------5 PRE--------------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FixedNumberPreConnector(5,weight,delay)
        #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))


    def test_generate_synapse_list_pre_6(self):
        with self.assertRaises(Exception):
            print "-----------------6 PRE--------------------"
            number_of_neurons = 5
            onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
            twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
            weight = 2
            delay = 1
            synapse_type = onep.vertex.get_synapse_id('excitatory')
            one_to_one_c = connectors.FixedNumberPreConnector(6,weight,delay)
            #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
            synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)

    def test_generate_synapse_list_pre_negative(self):
        with self.assertRaises(Exception):
            print "---------------|-1 PRE|-------------------"
            number_of_neurons = 5
            onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
            twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
            weight = 2
            delay = 1
            synapse_type = onep.vertex.get_synapse_id('excitatory')
            one_to_one_c = connectors.FixedNumberPreConnector(-1,weight,delay)
            #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
            synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)

    def test_allow_self_connections(self):
        with self.assertRaises(Exception):
            print "--------------SELF CONNECTION-------------------"
            number_of_neurons = 5
            onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
            twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
            weight = 2
            delay = 1
            synapse_type = onep.vertex.get_synapse_id('excitatory')
            one_to_one_c = connectors.FixedNumberPreConnector(5,weight,delay,allow_self_connections = False)
            synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)



if __name__=="__main__":
    unittest.main()
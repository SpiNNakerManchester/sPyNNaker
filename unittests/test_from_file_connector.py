#!/usr/bin/env python
import unittest
import pacman103.front.pynn as pynn
import pacman103.front.pynn.connectors as connectors
from pprint import pprint as pp
#Setup
pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
nNeurons = 10
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
class TestingFromListConnector(unittest.TestCase):
    def test_generate_synapse_list_simulated_all_to_all(self):
        print "-------------------All To All from List------------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        connection_list = list()
        for i in range(5):
            for j in range(5):
                connection_list.append((i,j,weight,delay))

        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FromListConnector(connection_list)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        #pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))


    def test_synapse_list_generation_simulated_one_to_one_larger_to_smaller(self):
        print "-------------One To One from List-----smaller to larger----------"
        number_of_neurons = 10
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons + 5,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        connection_list= list()
        for i in range(number_of_neurons):
            connection_list.append((i,i,weight,delay))
        one_to_one_c = connectors.FromListConnector(connection_list)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,twop.vertex,1,0)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))


    def test_synapse_list_generation_for_simulated_one_to_one_smaller_to_larger(self):
        with self.assertRaises(Exception):
            print "-------------One To One from List-----larger to smaller----------"
            number_of_neurons = 10
            onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
            twop=pynn.Population(number_of_neurons + 5,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
            weight = 2
            delay = 1
            connection_list= list()
            for i in range(number_of_neurons + 5):
                connection_list.append((i,i,weight,delay))
            one_to_one_c = connectors.FromListConnector(connection_list)
            synaptic_list = one_to_one_c.generate_synapse_list(twop.vertex,onep.vertex,1,0)
            #pp(synaptic_list.get_rows())
            #self.assertEqual(synaptic_list.get_max_weight(),weight)
            #self.assertEqual(synaptic_list.get_min_weight(),weight)
            #self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons + 5)
            #self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))

    def test_not_safe(self):
        print "-------------------Not safe-----------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        connection_list = list()
        for i in range(5):
            for j in range(5):
                connection_list.append((i,j,weight,delay))

        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FromListConnector(connection_list, safe = False)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        #pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))


    def test_verbose(self):
        print "-------------------Verbose------------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        connection_list = list()
        for i in range(5):
            for j in range(5):
                connection_list.append((i,j,weight,delay))

        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FromListConnector(connection_list, verbose = True)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        #pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))

    def test_not_safe_and_verbose(self):
        print "--------------Not safe & Verbose------------"
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        connection_list = list()
        for i in range(5):
            for j in range(5):
                connection_list.append((i,j,weight,delay))

        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.FromListConnector(connection_list, safe = False, verbose= True)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        #pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))

if __name__=="__main__":
    unittest.main()
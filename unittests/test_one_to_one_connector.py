#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pynn
#Setup
pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
nNeurons = 10
weight = 2
delay = 5
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
class TestingOneToOneConnector(unittest.TestCase):
    def test_generate_synapse_list(self):
        number_of_neurons = 10
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = pynn.OneToOneConnector(weight,delay)
        #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        #pp(synaptic_list.get_rows())
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))

    def test_synapse_list_generation_for_null_populations(self):
        weight = 2
        delay = 1
        zp = pynn.Population(0,pynn.IF_curr_exp,cell_params_lif,label="Zero pop")
        one_to_one_c = pynn.OneToOneConnector(weight,delay)
        number_of_neurons = 10
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        zero_synaptic_list = one_to_one_c.generate_synapse_list(zp.vertex,onep.vertex,1,0)
        #pp(zero_synaptic_list.get_rows())
        """
        self.assertEqual(zero_synaptic_list.get_max_weight(),weight)
        self.assertEqual(zero_synaptic_list.get_min_weight(),weight)

        self.assertEqual(zero_synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(zero_synaptic_list.get_min_max_delay(),(delay,delay))
        """

    def test_synapse_list_generation_for_different_sized_populations(self):
        number_of_neurons = 10
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons + 5,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        one_to_one_c = pynn.OneToOneConnector(weight,delay)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,twop.vertex,1,0)
        self.assertEqual(synaptic_list.get_max_weight(),weight)
        self.assertEqual(synaptic_list.get_min_weight(),weight)
        self.assertEqual(synaptic_list.get_n_rows(),number_of_neurons)
        self.assertEqual(synaptic_list.get_min_max_delay(),(delay,delay))

    def test_synapse_list_(self):
        number_of_neurons = 10
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")

if __name__=="__main__":
    unittest.main()
#!/usr/bin/env python
import unittest
import pacman103.front.pynn.connectors as connectors
import pacman103.front.pynn as pynn
from pprint import pprint as pp
populations = list()
cell_params_lif = {
    'cm'  : 0.25, 
    'i_offset'  : 0.0,
    'tau_m'     : 20.0,
    'tau_refrac': 2.0,
    'tau_syn_E' : 5.0,
    'tau_syn_I' : 5.0,
    'v_reset'   : -70.0,
    'v_rest'    : -65.0,
    'v_thresh'  : -50.0
                     }
pynn.setup(timestep=1,min_delay = 1, max_delay = 10)
populations.append(pynn.Population(5,pynn.IF_curr_exp,cell_params_lif,label="First normal pop" ))
populations.append(pynn.Population(10,pynn.IF_curr_exp,cell_params_lif,label="Second normal pop" ))
populations.append(pynn.Population(0,pynn.IF_curr_exp,cell_params_lif,label="Zero pop" ))
populations.append(pynn.Population(-1,pynn.IF_curr_exp,cell_params_lif,label="First negative pop" ))
populations.append(pynn.Population(-5,pynn.IF_curr_exp,cell_params_lif,label="Second negative pop" ))
weight , delay = 5, 5
projections= list()
class MultapseConnectorTest(unittest.TestCase):
    def test_a(self):
        projections.append(pynn.Projection(populations[0],populations[1],pynn.MultapseConnector(
            numSynapses=5, weights= weight, delays= delay )))

    def test_nasty(self):
        projections.append(pynn.Projection(populations[0],populations[1],pynn.MultapseConnector(
            numSynapses=10,weights= weight,delays= delay)))

    def test_generate_synaptic_list(self):
        number_of_neurons = 5
        onep=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label="One pop")
        twop=pynn.Population(number_of_neurons,pynn.IF_curr_exp,cell_params_lif,label= "Second pop")
        weight = 2
        delay = 1
        synapse_type = onep.vertex.get_synapse_id('excitatory')
        one_to_one_c = connectors.MultapseConnector(1,weight,delay)
        #def generate_synapse_list(self, prevertex, postvertex, delay_scale, synapse_type)
        synaptic_list = one_to_one_c.generate_synapse_list(onep.vertex,onep.vertex,1,synapse_type)
        pp(synaptic_list.get_rows())


if __name__ == "__main__":
        unittest.main()
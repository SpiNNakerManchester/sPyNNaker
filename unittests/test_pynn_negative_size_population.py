#!/usr/bin/env python
import unittest
import pacman103
import pacman103.front.pynn.models as models
import numpy, pylab
import boot

import pacman103.front.pynn as pynn
populations = list()
cell_params_lif = dict()
class TestingPopulation(unittest.TestCase):
    def test(self):
        """
        Testing the Population object's methods
        """
        print "Creating populations "
        pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
        global populations, cell_params_lif
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


        """
        Creating new populations with different models
        """

        populations.append(pynn.Population(1,pynn.IF_curr_exp,cell_params_lif, label="One population"))
        populations.append(pynn.Population(nNeurons,pynn.IF_curr_exp,cell_params_lif,label="i&f"))
        """
        These should raise an Exception
                                            |
                                            |
                                            v
        """
        populations.append(pynn.Population(-1,pynn.IF_curr_exp,cell_params_lif,label="-1"))
        populations.append(pynn.Population(-10,pynn.IF_curr_exp,cell_params_lif,label="-10"))
        populations.append(pynn.Population( 0,pynn.IF_curr_exp,cell_params_lif,label="0"))

        #populations.append(pynn.Population(nNeurons,pynn.IF_curr_dual_exp,cell_params_lif,label="i&f"))
        """
        Adding a population to another one -- Not implemented yet
        """
        #print "Adding a population to another one"
        #population0.__add__(population1)
        """
        Retrieving the neuron at the specified index from the population -- Not implemented yet
        """
        #neuron = population1[0]
        #or
        #neuron = population1.__getitem__(0)
        """
        Iterating over populations -- Not implemented yet
        """   
        #for neuron in population1:
        #    continue
        
        """
        all method of population -- Not implemented yet
        """
        #neurons = population1.all()
        """
        can_record(variable) method of population -- Not implemented yet
        """

        """
        describe the population 
        """
    
    def test_run_negative_size_population_alone(self):
        print "---------------NEGATIVE SIZE POPULATION SIMULATION W/O PROJECTIONS------------------"
        global populations
        if pynn.controller is None:
            pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
        pynn.set_number_of_neurons_per_core("IF_curr_exp", 250)
        weight_to_spike = 2
        delay = 5
        populations[3].record()
        pynn.run(1000)
        spikes = populations[3].getSpikes(compatible_output=True)
        print spikes
        pynn.end()
        print "-----///////////NEGATIVE SIZE POPULATION SIMULATION W/O PROJECTIONS------------------"


if __name__=="__main__":
    unittest.main()
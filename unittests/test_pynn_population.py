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
    def test_population_variables(self):
        print "Testing populations cellclass"
        assert  isinstance(populations[0].vertex,models.IF_curr_exp)
        assert  isinstance(populations[1].vertex,models.IF_curr_exp)
        pynn.setup()
        spikeArray = {'spike_times': [[0]]}
        initial = pynn.Population(1, pynn.SpikeSourceArray, spikeArray, label='inputSpikes_2')
        assert isinstance(initial.vertex,models.SpikeSourceArray)

        print "Testing population cellclass arguments"
        for index in range(2):
            self.assertEqual(populations[index].vertex.tau_m , cell_params_lif['tau_m'])
            self.assertEqual(populations[index].vertex.cm , cell_params_lif['cm'])
            self.assertEqual(populations[index].vertex.v_rest , cell_params_lif['v_rest'])
            self.assertEqual(populations[index].vertex.v_reset , cell_params_lif['v_reset'])
            self.assertEqual(populations[index].vertex.v_thresh , cell_params_lif['v_thresh'])
            self.assertEqual(populations[index].vertex.tau_refrac , cell_params_lif['tau_refrac'])
            self.assertEqual(populations[index].vertex.i_offset , cell_params_lif['i_offset'])
            #self.assertEqual(populations[index].vertex.v_init , cell_params_lif['v_init'])
            self.assertEqual(populations[index].vertex.tau_syn_E , cell_params_lif['tau_syn_E'])
            self.assertEqual(populations[index].vertex.tau_syn_I , cell_params_lif['tau_syn_I'])
        
    def test_run_negative_size_population(self):
        print "---------------NEGATIVE SIZE POPULATION SIMULATION W/ PROJECTIONS------------------"
        global populations
        if pynn.controller is None:
            pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
        pynn.set_number_of_neurons_per_core("IF_curr_exp", 250)
        weight_to_spike = 2
        delay = 5
        injectionConnection = [(0, 0, weight_to_spike, delay)]
        spikeArray = {'spike_times': [[0]]}
        initial_spike=pynn.Population(1, pynn.SpikeSourceArray, spikeArray, label='inputSpikes_1')
        connectionList = list()
        populations[3].record()
        connectionList.append(pynn.Projection(initial_spike,populations[3],pynn.AllToAllConnector(weight_to_spike,delay)))
        connectionList.append(pynn.Projection(populations[3],populations[3],pynn.OneToOneConnector(weight_to_spike,delay)))
        pynn.run(1000)
        spikes = populations[3].getSpikes(compatible_output=True)
        print spikes
        pynn.end()

    def test_population_size(self):
        """
        Size of populations
        """
        print "Testing populations sizes"
        self.assertEqual(populations[0].__len__(),1)
        self.assertEqual(populations[1].__len__(),10)
        self.assertEqual(populations[0].size, 1)
        self.assertEqual(populations[1].size,10)

    def test_population_size(self):
        """
        Size of populations
        """
        print "Testing populations sizes"
        self.assertEqual(populations[0].__len__(),1)
        self.assertEqual(populations[1].__len__(),10)
        self.assertEqual(populations[0].size, 1)
        self.assertEqual(populations[1].size,10)
        
        
    def test_negative_size(self):
        global populations
        print "Testing populations of negative sizes"
        self.assertEqual(populations[2].__len__() , -1)
        self.assertEqual(populations[3].__len__() , -10)
        self.assertEqual(populations[2].size ,  -1)
        self.assertEqual(populations[3].size , -10)
        self.assertEqual(populations[4].size , 0)
        self.assertEqual(populations[4].__len__() , 0)
       
    def test_get_spikes_population(self):
        """
        Test should capture spikes that happened on the SpiNNaker board 
        """
        print "-----------------------SPIKE ARRAY-------------------------"
        global populations
        if pynn.controller is None:
            pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
        pynn.set_number_of_neurons_per_core("IF_curr_exp", 250)
        weight_to_spike = 2
        delay = 5
        injectionConnection = [(0, 0, weight_to_spike, delay)]
        spikeArray = {'spike_times': [[0]]}
        initial_spike=pynn.Population(1, pynn.SpikeSourceArray, spikeArray, label='inputSpikes_1')
        projections = list()
        #Populations must be recording in order to see spikes
        populations[0].record()
        #connectionList.append(pynn.Projection(initial_spike,populations[1],pynn.FromListConnector(injectionConnection)))
        projections.append(pynn.Projection(initial_spike,populations[0],pynn.AllToAllConnector(weight_to_spike,delay)))
        #projections.append(pynn.Projection(populations[0],populations[0],pynn.OneToOneConnector(weight_to_spike,delay)))
        projections.append(pynn.Projection(populations[0],populations[0],pynn.FromListConnector(injectionConnection)))
        pynn.run(20)

        spikes = None
        spikes = populations[0].getSpikes(compatible_output=True)
        print spikes
        pynn.end()
        #This test has to be rewritten as I know this works


if __name__=="__main__":
    unittest.main()
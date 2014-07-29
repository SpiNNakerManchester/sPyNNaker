#!/usr/bin/env python
import unittest
import spynnaker.pyNN as pynn
import spynnaker.pyNN.models.neural_models as models
from spynnaker.pyNN.models.neural_models.izk_curr_exp import IzhikevichCurrentExponentialPopulation
from spynnaker.pyNN.exceptions import ConfigurationException
import numpy, pylab

populations = list()
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
cell_params_izk= {
    'a' :0.02,
    'c' :-65.0,
    'b' :0.2,
    'd' :2.0,
    'i_offset' :0,
    'u_init' :-14.0,
    'v_init' :-70.0,
    'tau_syn_E' :5.0,
    'tau_syn_I' :5.0

}
pynn.setup(timestep=1, min_delay=1, max_delay=10.0)
class TestingPopulation(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_if_curr_exp_population(self):
        pynn.Population(1,pynn.IF_curr_exp,cell_params_lif, label="One population")

    def test_create_if_cond_exp_population(self):
        pynn.Population(1,pynn.IF_cond_exp,{}, label="One population")

    def test_create_izk_curr_exp_population(self):
        pynn.Population(1,IzhikevichCurrentExponentialPopulation,cell_params_izk, label="One population")

    def test_create_if_curr_dual_exp_population(self):
        pynn.Population(1,pynn.IF_curr_dual_exp,cell_params_lif, label="One population")

    def test_create_if_curr_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pynn.Population(0,pynn.IF_curr_exp,cell_params_lif, label="One population")

    def test_create_if_cond_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pynn.Population(0,pynn.IF_cond_exp,{}, label="One population")

    def test_create_izk_curr_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pynn.Population(0,IzhikevichCurrentExponentialPopulation,cell_params_izk, label="One population")

    def test_create_if_curr_dual_exp_population_zero(self):
        with self.assertRaises(ConfigurationException):
            pynn.Population(0,pynn.IF_curr_dual_exp,cell_params_lif, label="One population")

    def test(self):
        """
        Testing the Population object's methods
        """
        print "Creating populations "

        global populations, cell_params_lif
        nNeurons = 10



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

    def test_population_variables(self):
        print "Testing populations cellclass"
        assert  isinstance(populations[0].vertex,models.if_curr_exp.IF_curr_exp)
        assert  isinstance(populations[1].vertex,models.if_curr_exp.IF_curr_exp)
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
        spikes = populations[3].get_spikes(compatible_output=True)
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
        spikes = populations[0].get_spikes(compatible_output=True)
        print spikes
        pynn.end()
        #This test has to be rewritten as I know this works


if __name__=="__main__":
    unittest.main()
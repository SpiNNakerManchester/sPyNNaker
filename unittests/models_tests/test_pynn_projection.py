#!/usr/bin/env python
import unittest
import spynnaker.pyNN.exceptions as exc
import spynnaker.pyNN as pynn

projections = list()
populations = list()
no_neurons = 10
projection_details = list()
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
cell_params_lif2exp = cell_params_lif
cell_params_lifexp={
    'tau_refrac':   0.1,
    'cm'        :   1.0,
    'tau_syn_E' :   5.0,
    'v_rest'    :   -65.0,
    'tau_syn_I' :   5.0,
    'tau_m'     :   20.0,
    'e_rev_E'   :   0.0,
    'i_offset'  :   0.0,
    'e_rev_I'   :   -70.0,
    'v_thresh'  :   -50.0,
    'v_reset'   :   -65.0    
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
spike_array = {'spike_times':[0]}
spike_array_poisson = {
    'duration'  :  10000000000.0,
    'start'     :  0.0,
    'rate'      :  1.0
}
cell_params_cochlea = {
    
}
cell_params_retina = {
    
}
cell_params_motor = {
    
}
cell_params_multicast = {
    
}
pynn.setup(timestep=1, min_delay=1, max_delay=15.0)
class TestProjection(unittest.TestCase):
    """
    Test the Projection class
    """

    def test_setup(self):
        global projections
        weight_to_spike = 2
        delay = 5
        populations.append(pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop"))
        populations.append(pynn.Population(no_neurons,pynn.IF_curr_dual_exp,cell_params_lif2exp,label="IF_curr_dual_exp Pop"))
        populations.append(pynn.Population(no_neurons,pynn.IF_cond_exp,cell_params_lifexp,label="IF_cond_exp Pop"))
        populations.append(pynn.Population(no_neurons,pynn.IZK_curr_exp,cell_params_izk,label="IZK_curr_exp Pop"))
        populations.append(pynn.Population(no_neurons,pynn.SpikeSourceArray,spike_array,label="SpikeSourceArray Pop"))
        populations.append(pynn.Population(no_neurons,pynn.SpikeSourcePoisson,spike_array_poisson,label="SpikeSourcePoisson Pop"))
        #populations.append(pynn.Population(no_neurons,pynn.ExternalCochleaDevice,cell_params_cochlea,label="ExternalCochleaDevice Pop"))
        #populations.append(pynn.Population(no_neurons,pynn.ExternalRetinaDevice,cell_params_retina,label="ExternalRetinaDevice Pop"))
        #populations.append(pynn.Population(no_neurons,pynn.ExternalMotorDevice,cell_params_motor,label="ExternalMotorDevice Pop"))
        #populations.append(pynn.Population(no_neurons,pynn.MultiCastSource,cell_params_multicast,label="MultiCastSource Pop"))

        for i in range(4):
            projection_details.append({'presyn':populations[0], 'postsyn':populations[i],'connector':pynn.OneToOneConnector(weight_to_spike,delay) })
            projections.append(pynn.Projection(populations[0],populations[i],pynn.OneToOneConnector(weight_to_spike,delay)))

    def test_source_populations_as_postsynaptic(self):
        '''
        This test should fail
        '''
        global projections
        weight_to_spike = 2
        delay = 5
        try:
            for i in range(4,6):
                projections.append(pynn.Projection(populations[0],populations[i],pynn.OneToOneConnector(weight_to_spike,delay)))
            raise EnvironmentError 
        except Exception as e:
            self.assertIsInstance(e,exc.ConfigurationException)

    def test_delays(self):
        global projections
        for p in projections:
            self.assertEqual(p.getDelays(),5)

    def test_weights(self):
        #print projections[1].getWeights()
        for p in projections:
            self.assertEqual(p.getWeights(),[2] * no_neurons)

    def test_projection_params(self):
        populations = list()
        projection_details = list()
        populations = list()
        weight_to_spike = 2
        delay = 5
        populations.append(pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop"))
        populations.append(pynn.Population(no_neurons,pynn.IF_curr_dual_exp,cell_params_lif2exp,label="IF_curr_dual_exp Pop"))
        populations.append(pynn.Population(no_neurons,pynn.IF_cond_exp,cell_params_lifexp,label="IF_cond_exp Pop"))
        populations.append(pynn.Population(no_neurons,pynn.IZK_curr_exp,cell_params_izk,label="IZK_curr_exp Pop"))

        for i in range(4):
            for j in range(4):
                projection_details.append({'presyn':populations[i], 'postsyn':populations[j],'connector':pynn.OneToOneConnector(weight_to_spike,delay) })
                projections.append(pynn.Projection(populations[i],populations[j],pynn.OneToOneConnector(weight_to_spike,delay)))

        for i in range(4):
            for j in range(4):
                self.assertEqual(projections[i + j]._projection_edge._pre_vertex , projection_details[i + j]['presyn']._vertex)
                self.assertEqual(projections[i + j]._projection_edge._post_vertex , projection_details[i + j]['postsyn']._vertex)
                #self.assertEqual(projections[i].connector , projection_details[i]['connector'])

    def test_inhibitory_connector(self):
        weight_to_spike = 2
        delay = 5
        p1 = pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop")
        p2 = pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop")
        
        s12_2 = pynn.Projection(p1,p2,pynn.OneToOneConnector(weight_to_spike,delay),target='inhibitory')
        s21 = pynn.Projection(p2,p1,pynn.OneToOneConnector(weight_to_spike,delay),target='excitatory')
        

    def test_one_to_one_connector_from_low_to_high(self):
        try:
            weight_to_spike,delay = 2, 5
            first_population = pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop")
            different_population = pynn.Population(20,pynn.IF_curr_exp,cell_params_lif,label="A random sized population")
            pynn.Projection(first_population,different_population,pynn.OneToOneConnector(weight_to_spike,delay))
            raise EnvironmentError(" OneToOneConnector between 2 different sized populations should have failed ")
        except Exception as e:
            self.assertIsInstance(e,exc.ConfigurationException)

    def test_one_to_one_connector_from_high_to_low(self):
        try:
            weight_to_spike,delay = 2, 5
            second_population = pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop")
            different_population = pynn.Population(20,pynn.IF_curr_exp,cell_params_lif,label="A random sized population")
            pynn.Projection(different_population,second_population,pynn.OneToOneConnector(weight_to_spike,delay))
            raise EnvironmentError(" OneToOneConnector between 2 different sized populations should have failed ")
        except Exception as e:
            self.assertIsInstance(e,exc.ConfigurationException)
            
    def test_all_to_all_connector(self):
        pass

    def test_all_to_all_connector_from_zero(self):
        pass

    def test_fixed_probability_connector(self):
        pass

    def test_fixed_number_pre_connector(self):
        pass

    def test_from_list_connector(self):
        pass

    def test_from_file_connector(self):
        pass

if __name__=="__main__":
    unittest.main()

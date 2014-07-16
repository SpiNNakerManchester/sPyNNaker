#!/usr/bin/env python
import unittest
import pacman103

import pacman103.core.exceptions as exc
import pacman103.front.pynn as pynn
import pylab

projections = list()
populations = list()
nNeurons = no_neurons = 10
projection_details = list()
weight_to_spike = 2
delay = 2
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
pynn.setup(timestep=1, min_delay=1, max_delay=15.0)
populations.append(pynn.Population(no_neurons,pynn.IF_curr_exp,cell_params_lif,label="LIF Pop"))
populations.append(pynn.Population(no_neurons,pynn.IZK_curr_exp,cell_params_izk,label="IZK_curr_exp Pop"))
populations.append(pynn.Population(no_neurons,pynn.SpikeSourceArray,spike_array,label="SpikeSourceArray Pop"))
projections.append(pynn.Projection(populations[0],populations[1],pynn.OneToOneConnector(weight_to_spike,delay)))
projections.append(pynn.Projection(populations[1],populations[0],pynn.OneToOneConnector(weight_to_spike,delay)))
projections.append(pynn.Projection(populations[2],populations[0],pynn.AllToAllConnector(weight_to_spike,delay)))   
class TestProjection(unittest.TestCase):  
    def test(self):
        for p in populations:
            p.record()
        populations[1].record_v()
        populations[1].record_gsyn()
        pynn.run(20)
        v = None
        gsyn = None
        spikes = None

        v = populations[1].get_v(compatible_output=True)
        gsyn = populations[1].get_gsyn(compatible_output=True)
        spikes = populations[1].get_spikes(compatible_output=True)

        if spikes != None:
            print spikes
            pylab.figure()
            pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".") 
            pylab.xlabel('Time/ms')
            pylab.ylabel('spikes')
            pylab.title('spikes')
            pylab.show()
        else:
            print "No spikes received"

        # Make some graphs
        ticks = len(v) / nNeurons

        if v != None:
            pylab.figure()
            pylab.xlabel('Time/ms')
            pylab.ylabel('v')
            pylab.title('v')
            for pos in range(0, nNeurons, 20):
                v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
                pylab.plot([i[1] for i in v_for_neuron], 
                        [i[2] for i in v_for_neuron])
            pylab.show()

        if gsyn != None:
            pylab.figure()
            pylab.xlabel('Time/ms')
            pylab.ylabel('gsyn')
            pylab.title('gsyn')
            for pos in range(0, nNeurons, 20):
                gsyn_for_neuron = gsyn[pos * ticks : (pos + 1) * ticks]
                pylab.plot([i[1] for i in gsyn_for_neuron], 
                        [i[2] for i in gsyn_for_neuron])
            pylab.show()
        pynn.end()

if __name__=="__main__":
    unittest.main()

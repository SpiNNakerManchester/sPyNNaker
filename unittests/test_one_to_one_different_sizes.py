#!/usr/bin/env python
import unittest
from spynnaker.pyNN.utilities.constants import VISUALISER_MODES as modes
import pylab, numpy
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
p_initial_spike = pynn.Population(1,pynn.SpikeSourceArray,spike_array,label="Initial spike pop")

p_initial_spike.record()
p1 = pynn.Population(10,pynn.IF_curr_exp,cell_params_lif,label="pop 1")
p2 = pynn.Population(5, pynn.IF_curr_exp, cell_params_lif,label="pop 2")
pr_12 = pynn.Projection(p1,p2,pynn.OneToOneConnector(weight,delay))
pr_21 = pynn.Projection(p2,p1,pynn.OneToOneConnector(weight,delay))
pr_initial = pynn.Projection(p_initial_spike,p1,pynn.AllToAllConnector(weight,delay))
p1.record()
p2.record() 
#/Setup



class TestingOneToOneConnectorForDifferentSizes(unittest.TestCase):

    def test_simulation(self):        
        p1.record_v()
        p1.record_gsyn()
        p1.record(visualiser_mode=modes.RASTER)
        pynn.run(200)
        v = None
        gsyn = None
        spikes = None

        v = p1.get_v(compatible_output=True)
        gsyn = p1.get_gsyn(compatible_output=True)
        spikes = p1.get_spikes(compatible_output=True)

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
        ticks = len(v) / 1

        if v != None:
            pylab.figure()
            pylab.xlabel('Time/ms')
            pylab.ylabel('v')
            pylab.title('v')
            for pos in range(0, 1, 20):
                v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
                pylab.plot([i[1] for i in v_for_neuron], 
                        [i[2] for i in v_for_neuron])
            pylab.show()

        if gsyn != None:
            pylab.figure()
            pylab.xlabel('Time/ms')
            pylab.ylabel('gsyn')
            pylab.title('gsyn')
            for pos in range(0, 1, 20):
                gsyn_for_neuron = gsyn[pos * ticks : (pos + 1) * ticks]
                pylab.plot([i[1] for i in gsyn_for_neuron], 
                        [i[2] for i in gsyn_for_neuron])
            pylab.show()

        pynn.end()


if __name__=="__main__":
    unittest.main()
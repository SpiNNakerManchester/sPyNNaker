#!/usr/bin/env python
import unittest
import pacman103

import pacman103.core.exceptions as exc
import pacman103.front.pynn as p
import visualiser.visualiser_modes as modes
import numpy, pylab

class TestInhibitoryProjection(unittest.TestCase):

    def test_inhibitory_connector_memory(self):
        p.setup(timestep=0.1, min_delay=1, max_delay=10.0)
        weight_to_spike = 10
        delay = 1
        cell_params_lif = {
            'cm'        : 0.25, 
            'i_offset'  : 0.0,
            'tau_m'     : 20.0,
            'tau_refrac': 1.0,
            'tau_syn_E' : 5.0,
            'tau_syn_I' : 8.0,
            'v_reset'   : -70.0,
            'v_rest'    : -65.0,
            'v_thresh'  : -50.0
                     }
        spike_array = {'spike_times':[0]}
        mem_access = {'spike_times':[10]}

        p_initial_spike = p.Population(1,p.SpikeSourceArray,spike_array,label="Initial spike pop")
        p_mem = p.Population(1,p.IF_curr_exp, cell_params_lif, label="Memory")
        p_out = p.Population(1,p.IF_curr_exp, cell_params_lif, label="Output")
        p_bridge = p.Population(1,p.IF_curr_exp, cell_params_lif, label="Bridge")
        p_inhibitor = p.Population(1,p.IF_curr_exp, cell_params_lif, label="Inhibitor")
        p_access = p.Population(1,p.SpikeSourceArray, mem_access, label="Access memory spike pop")


        p_out.record()
        p_mem.record()
        p_inhibitor.record()
        p_initial_spike.record()
        p_access.record()
        

        pr_initial_spike1 = p.Projection(p_initial_spike,p_mem,p.OneToOneConnector(weight_to_spike,delay))
        pr_initial_spike2 = p.Projection(p_initial_spike,p_inhibitor,p.OneToOneConnector(weight_to_spike,delay))

        pr_mem_access = p.Projection(p_access,p_inhibitor,p.OneToOneConnector(weight_to_spike,delay), target= 'inhibitory')

        pr_inhibitor_self = p.Projection(p_inhibitor,p_inhibitor,p.OneToOneConnector(weight_to_spike,delay))
        pr_inhibitor_bridge = p.Projection(p_inhibitor,p_bridge,p.OneToOneConnector(weight_to_spike,delay), target= 'inhibitory')

        pr_mem_self = p.Projection(p_mem,p_mem,p.OneToOneConnector(weight_to_spike,delay))
        pr_mem_bridge = p.Projection(p_mem,p_bridge,p.OneToOneConnector(weight_to_spike,delay))

        pr_bridge_output = p.Projection(p_bridge,p_out,p.OneToOneConnector(weight_to_spike,delay))

        pr_bridge_inhibitor = p.Projection(p_bridge,p_inhibitor,p.OneToOneConnector(weight_to_spike,delay))
        

        p_mem.record_v()
        p_mem.record_gsyn()
        p_mem.record(visualiser_mode=modes.RASTER)
        p.run(30)

        v = None
        gsyn = None
        spikes = None

        v = p_mem.get_v(compatible_output=True)
        gsyn = p_mem.get_gsyn(compatible_output=True)
        spikes = p_mem.getSpikes(compatible_output=True)

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

        p.end()

if __name__=="__main__":
    unittest.main()
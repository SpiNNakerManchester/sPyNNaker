#!/usr/bin/env python


import pyNN.spiNNaker as p

from pylab import *

p.setup(timestep=1.0,min_delay=1.0,max_delay=1.0)

cell_params = {     'i_offset' : .1,    'tau_refrac' : 3.0, 'v_rest' : -65.0,
                    'v_thresh' : -51.0,  'tau_syn_E'  : 2.0,
                    'tau_syn_I': 5.0,    'v_reset'    : -70.0,
                    'e_rev_E'  : 0.,     'e_rev_I'    : -80.}


  # setup test population
if_pop = p.Population(1,p.IF_cond_exp,cell_params)
# setup spike sources
exc_pop = p.Population(1,p.SpikeSourceArray,{'spike_times':[20.,40.,60.]})
inh_pop = p.Population(1,p.SpikeSourceArray,{'spike_times':[120.,140.,160.]})
# setup excitatory and inhibitory connections
listcon = p.FromListConnector([(0,0,0.01,1.0)])
exc_pro = p.Projection(exc_pop,if_pop,listcon,target='excitatory')
inh_pro = p.Projection(inh_pop,if_pop,listcon,target='inhibitory')
# setup recorder
if_pop.record_v()
p.run(200.)
#read out voltage and plot
V = if_pop.get_v()
plot(V[:,1],V[:,2],'.',label=p.__name__)
p.end()

legend()
show()
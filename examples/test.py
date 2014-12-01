"""
Synfirechain-like example
"""
#!/usr/bin/python
import os
import spynnaker.pyNN as p
import numpy, pylab
from pyNN.random import NumpyRNG, RandomDistribution

nNeurons = 1

p.setup( timestep = 1.0, min_delay = 1.0, max_delay = 16.0 )

cell_params_lif = {  'cm'        : 1.0, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 20.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 5.0,
                     'tau_syn_I' : 5.0,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -50.0
                     }

cell_params_pos = {
'rate'  : 10.0
}

rng = NumpyRNG( seed = 1 )
weight_distn = RandomDistribution( 'normal', parameters = [ 0.35, 0.035 ], rng=rng, boundaries=[0.0, 3.0 ], constrain='redraw' )
delay_distn = RandomDistribution( 'normal', parameters = [ 7.0, 2.0 ], rng=rng, boundaries=[1.0, 16.0], constrain='redraw' )

sink = p.Population( nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1')

source = p.Population( 2000, p.SpikeSourcePoisson, cell_params_pos, label='inputSpikes_1')

p.Projection( source, sink, p.AllToAllConnector( weights = weight_distn, delays = delay_distn ))

sink.record_v()
sink.record_gsyn()
sink.record()

run_time = 1000
print "Running for {} ms".format(run_time)
p.run(run_time)

v = None
gsyn = None
spikes = None

v = sink.get_v(compatible_output=True)
gsyn = sink.get_gsyn(compatible_output=True)
spikes = sink.getSpikes(compatible_output=True)
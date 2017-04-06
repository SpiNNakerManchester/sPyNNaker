"""
A single IF neuron with exponential, conductance-based synapses, fed by two
spike sources.

Run as:

$ python IF_cond_exp.py <simulator>

where <simulator> is 'neuron', 'nest', etc

Andrew Davison, UNIC, CNRS
May 2006

$Id: IF_cond_exp.py 917 2011-01-31 15:23:34Z apdavison $
"""

from pyNN.utility import get_script_args
from pyNN.errors import RecordingError

import spynnaker.pyNN as p

p.setup(timestep=1.0,min_delay=1.0,max_delay=10.0, db_name='if_cond.sqlite')



cell_params = {     'i_offset' : .1,    'tau_refrac' : 3.0, 'v_rest' : -65.0,
                    'v_thresh' : -51.0,  'tau_syn_E'  : 2.0,
                    'tau_syn_I': 5.0,    'v_reset'    : -70.0}

ifcell = p.Population(1, p.IF_curr_exp, cell_params, label='IF_curr_exp')

spike_sourceE = p.Population(1, p.SpikeSourceArray, {'spike_times': [[i for i in range(5,105,10)],]}, label='spike_sourceE')

p.Projection(spike_sourceE, ifcell, p.OneToOneConnector(weights=1, delays=2), target='excitatory')
breakMe = True
if breakMe:
	p.Projection(spike_sourceE, ifcell, p.OneToOneConnector(weights=1, delays=2), target='excitatory')

ifcell.record_v()
ifcell.record_gsyn()

p.run(200.0)

recorded_v =  ifcell.get_v()
recorded_gsyn =  ifcell.get_gsyn()



import pylab
f = pylab.figure()
f.add_subplot(211)
pylab.plot([ i[2] for i in recorded_v ])

f.add_subplot(212)
pylab.plot([ i[2] for i in recorded_gsyn ], color='green')

pylab.show()
p.end()


__author__ = 'stokesa6'
import spynnaker.pyNN as p

import visualiser.visualiser_constants as modes
import numpy as np, pylab
from pyNN.random import RandomDistribution, NumpyRNG

p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)

nNeurons = 200 # number of neurons in each population
neuron_model = p.IF_curr_exp(nNeurons, 1.0)
p.set_number_of_neurons_per_core("IF_curr_exp", 100)

cm = list()
i_off = list()
tau_m = list()
tau_re = list()
tau_syn_e = list()
tau_syn_i = list()
v_reset = list()
v_rest = list()
v_thresh = list()

for atom in range(0, nNeurons):
    cm.append(0.25)
    i_off.append(0.0)
    tau_m.append(10.0)
    tau_re.append(2.0)
    tau_syn_e.append(0.5)
    tau_syn_i.append(0.5)
    v_reset.append(-65.0)
    v_rest.append(-65.0)
    v_thresh.append(-64.4)

gbar_na_distr = RandomDistribution('normal', (20.0, 2.0), rng=NumpyRNG(seed=85524))

cell_params_lif = {'cm'          : cm, # nF
                     'i_offset'  : i_off,
                     'tau_m'     : tau_m,
                     'tau_refrac': tau_re,
                     'tau_syn_E' : tau_syn_e,
                     'tau_syn_I' : tau_syn_i,
                     'v_reset'   : v_reset,
                     'v_rest'    : v_rest,
                     'v_thresh'  : v_thresh
                   }

populations = list()
projections = list()

weight_to_spike = 2
#delay = 3.1
delay = 1

loopConnections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, delay)]
spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray, label='inputSpikes_1'))

populations[0].set('_cm', 0.25)
populations[0].set('_cm', cm)
populations[0].set('_tau_m', tau_m, '_v_thresh', v_thresh)
populations[0].set('_i_offset', gbar_na_distr)

populations[0].set(_cm=0.25)
populations[0].set(_cm=cm)
populations[0].set(_tau_m=tau_m, _v_thresh=v_thresh)
populations[0].set(_i_offset=gbar_na_distr)
populations[0].set(_i_offset=i_off)


#populations[0].set_mapping_constraint({"x": 1, "y": 0})

projections.append(p.Projection(populations[0], populations[0], p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[1], populations[0], p.FromListConnector(injectionConnection)))

populations[0].record_v()
populations[0].record_gsyn()
populations[0].record(visualiser_mode=modes.RASTER)

p.run(100)

v = populations[0].get_v(compatible_output=True)
gsyn = populations[0].get_gsyn(compatible_output=True)
spikes = populations[0].getSpikes(compatible_output=True)

if spikes != None:
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

p.end()
"""
Synfirechain-like example
"""
#!/usr/bin/python
import pylab

import spynnaker.pyNN as p

# todo christian needs to fix into intergration test

p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
nNeurons = 20  # number of neurons in each population

cell_params_lif = {'cm': 0.25,  # nF
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0}

populations = list()
projections = list()

weight_to_spike = 1.0
delay = 1
connections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    connections.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, 1)]
spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                label='pop_1'))
populations[0].add_placement_constraint(x=0, y=0, p=9)
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                label='inputSpikes_1'))

projections.append(p.Projection(populations[0], populations[0],
                                p.FromListConnector(connections)))
projections.append(p.Projection(populations[1], populations[0],
                                p.FromListConnector(injectionConnection)))
print "before"
delays = projections[0].getDelays()
weights = projections[0].getWeights()

p.run(100)

print delays
print weights

print "after"
delays = projections[0].getDelays()
weights = projections[0].getWeights()

print delays
print weights

v = None
gsyn = None
spikes = None

p.end()

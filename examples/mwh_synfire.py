"""
Synfirechain-like example
"""
#!/usr/bin/python
import os
import spynnaker.pyNN as p
#import pyNN.spiNNaker as p
import numpy, pylab

#p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
p.setup(timestep=1.0, min_delay = 1.0, max_delay = 144.0)
nNeurons = 10 # number of neurons in each population
max_delay = 50
#p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)
#p.set_number_of_neurons_per_core("DelayExtension", n_neurons / 2)


cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 20.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 5.0,
                     'tau_syn_I' : 5.0,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -50.0
                     }

populations = list()
projections = list()

weight_to_spike = 2.0
delay = 3
delays = list()

loopConnections = list()
for i in range(0, nNeurons):
    delays.append(float(delay))
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, 1)]
# spikeArray = {'spike_times': [[0]]}
i = [a*100 for a in xrange(30)]
spikeArray = {'spike_times': [i for _ in xrange(10)],
              'max_on_chip_memory_usage_for_spikes_in_bytes': 100}

populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1'))

populations.append(p.Population(10, p.SpikeSourceArray, spikeArray, label='inputSpikes_1'))
#populations[0].set_mapping_constraint({"x": 1, "y": 0})

projections.append(p.Projection(populations[0], populations[0], p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[1], populations[0], p.FromListConnector(injectionConnection)))

populations[0].record_v()
populations[0].record_gsyn()
populations[0].record()

run_time = 10000
print "Running for {} ms".format(run_time)
p.run(run_time)

v = None
gsyn = None
spikes = None
print(projections[0].getWeights())
print(projections[0].getDelays())
print delays

v = populations[0].get_v(compatible_output=True)
gsyn = populations[0].get_gsyn(compatible_output=True)
spikes = populations[0].getSpikes(compatible_output=True)

if spikes is not None:
   print spikes
   pylab.figure()
   pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
   pylab.xlabel('neuron id')
   pylab.ylabel('Time/ms')
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

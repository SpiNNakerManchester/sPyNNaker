"""
Synfirechain-like example
"""
#!/usr/bin/python
import spynnaker.pyNN as p
import visualiser_framework.visualiser_modes as modes
import numpy, pylab

p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
p.set_number_of_neurons_per_core("IF_curr_exp", 100)

nNeurons = 2 # number of neurons in each population

cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 10.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 0.5,
                     'tau_syn_I' : 0.5,
                     'v_reset'   : -65.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -64.4
                     }

populations = list()
projections = list()

weight_to_spike = 2
#delay = 3.1
injection_delay = 2
delay = 10

spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray, label='inputSpikes_1'))

projections.append(p.Projection(populations[0], populations[0], p.AllToAllConnector(weights=weight_to_spike, delays=delay)))
projections.append(p.Projection(populations[1], populations[0], p.FromListConnector([(0, 0, 4, injection_delay)])))

populations[0].record_v()
populations[0].record(visualiser_mode=modes.RASTER)

p.run(90)

v = None
gsyn = None
spikes = None

v = populations[0].get_v(compatible_output=True)
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

print v

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

p.end()
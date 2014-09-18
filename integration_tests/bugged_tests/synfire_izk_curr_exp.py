"""
Synfirechain-like example
"""
#!/usr/bin/python
import spynnaker.pyNN as p
import pylab

p.setup(timestep=1.0, min_delay = 1.0, max_delay = 32.0)
p.set_number_of_neurons_per_core("IZK_curr_exp", 100)

nNeurons = 200 # number of neurons in each population

cell_params_izk = {
    'a': 0.02,
    'b': 0.2,
    'c': -65,
    'd': 8,
    'v_init': -75,
    'u_init': 0,
    'tau_syn_E': 2,
    'tau_syn_I': 2,
    'i_offset': 0
    }

populations = list()
projections = list()

weight_to_spike = 40
delay = 1

loopConnections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)


injectionConnection = [(0, 0, weight_to_spike, delay)]
spikeArray = {'spike_times': [[50]]}
populations.append(p.Population(nNeurons, p.IZK_curr_exp, cell_params_izk, label='pop_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray, label='inputSpikes_1'))

projections.append(p.Projection(populations[0], populations[0], p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[1], populations[0], p.FromListConnector(injectionConnection)))

populations[0].record_v()
populations[0].record()

p.run(500)

v = None
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

if v != None:
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    print v
    for pos in range(0, nNeurons, 20):
    #for pos in range(0, nNeurons):
        v_for_neuron = v[pos * ticks : (pos + 1) * ticks]
        print v_for_neuron
        pylab.plot([i[1] for i in v_for_neuron], 
                [i[2] for i in v_for_neuron])
    pylab.show()

p.end()
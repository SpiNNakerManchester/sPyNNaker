


"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
import pylab

p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
nNeurons = 200  # number of neurons in each population
p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)


cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0
                   }

populations = list()
projections = list()
population_views = list()
assemblies = list()

weight_to_spike = 2.0
delay = 6

loopConnections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)

loopConnections2 = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections2.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, 1)]
type_connection = [(199, 0, weight_to_spike, 1)]
spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                   label='pop_1'))
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                   label='pop_2'))
input_population = p.Population(1, p.SpikeSourceArray, spikeArray,
                                label='inputSpikes_1')

#assemblies.append(p.Assembly(populations, "assemble"))
#assemblies[0].record()

populations[0].record()
populations[1].record()

projections.append(p.Projection(populations[0], populations[0],
                   p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[0], populations[1],
                   p.FromListConnector(type_connection)))
projections.append(p.Projection(populations[1], populations[1],
                   p.FromListConnector(loopConnections2)))
projections.append(p.Projection(input_population, populations[0],
                   p.FromListConnector(injectionConnection)))

p.run(5000)

spikes = populations[0].getSpikes(compatible_output=True)
spikes2 = populations[1].getSpikes(compatible_output=True)
spikes2 += nNeurons

#spikes = assemblies[0].getSpikes(compatible_output=True)

if spikes is not None:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.plot([i[1] for i in spikes2], [i[0] for i in spikes2], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

p.end()

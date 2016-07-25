
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
delay = 17

loopConnections = list()
for i in range(0, nNeurons):
    singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
    loopConnections.append(singleConnection)

injectionConnection = [(0, 0, weight_to_spike, 1)]
spikeArray = {'spike_times': [[0]]}
populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                   label='pop_1'))
populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                   label='inputSpikes_1'))

neuron_filter_1 = []
for x in range(20, 50):
    neuron_filter_1.append(x)

neuron_filter_2 = []
for x in range(120, 150):
    neuron_filter_2.append(x)


population_views.append(p.PopulationView(
    populations[0], neuron_filter_1, "pop_view_1"))
population_views.append(p.PopulationView(
    populations[0], neuron_filter_2, "pop_view_2"))

population_views[0].record()
population_views[1].record_v()

atom_mapping = populations[0]._spinnaker.get_pop_atom_mapping()
index = 0
atoms = atom_mapping[populations[0]._class][populations[0]]
for atom in atoms:
    if 50 > index > 20:
        if not atom.record_spikes:
            raise AssertionError("Pop view didnt set the atom correctly.")
    if 120 > index > 150:
        if not atom.record_v:
            raise AssertionError("Pop view didnt set the atom correctly.")
    index += 1


projections.append(p.Projection(populations[0], populations[0],
                   p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[1], populations[0],
                   p.FromListConnector(injectionConnection)))

populations[0].record_v()
populations[0].record_gsyn()
populations[0].record()

index = 0
for atom in atom_mapping[populations[0]._class][populations[0]]:
    if not atom.record_spikes:
        raise AssertionError("Pop didnt set the atom correctly.")
    if not atom.record_v:
        raise AssertionError("Pop didnt set the atom correctly.")
    if not atom.record_gsyn:
        raise AssertionError("Pop didnt set the atom correctly.")
    index += 1

p.run(5000)

v = None
gsyn = None
spikes = None

v = populations[0].get_v(compatible_output=True)
gsyn = populations[0].get_gsyn(compatible_output=True)
spikes = populations[0].getSpikes(compatible_output=True)

if spikes is not None:
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

if v is not None:
    ticks = len(v) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('v')
    pylab.title('v')
    for pos in range(0, nNeurons, 20):
        v_for_neuron = v[pos * ticks: (pos + 1) * ticks]
        pylab.plot([i[2] for i in v_for_neuron])
    pylab.show()

if gsyn is not None:
    ticks = len(gsyn) / nNeurons
    pylab.figure()
    pylab.xlabel('Time/ms')
    pylab.ylabel('gsyn')
    pylab.title('gsyn')
    for pos in range(0, nNeurons, 20):
        gsyn_for_neuron = gsyn[pos * ticks: (pos + 1) * ticks]
        pylab.plot([i[2] for i in gsyn_for_neuron])
    pylab.show()


spikes = population_views[0].getSpikes(compatible_output=True)

if spikes is not None:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

spikes = population_views[1].getSpikes(compatible_output=True)

if spikes is not None:
    print spikes
    pylab.figure()
    pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
    pylab.xlabel('Time/ms')
    pylab.ylabel('spikes')
    pylab.title('spikes')
    pylab.show()
else:
    print "No spikes received"

p.end()

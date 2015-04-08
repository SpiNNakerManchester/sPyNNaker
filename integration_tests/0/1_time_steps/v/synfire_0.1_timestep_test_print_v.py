"""
Synfirechain-like example
"""
import pyNN.spiNNaker as p
import pylab
import os


p.setup(timestep=0.1, min_delay=1.0, max_delay=14.40)
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

weight_to_spike = 2.0
delay = 1.7

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

projections.append(p.Projection(populations[0], populations[0],
                   p.FromListConnector(loopConnections)))
projections.append(p.Projection(populations[1], populations[0],
                   p.FromListConnector(injectionConnection)))

populations[0].record_v()
populations[0].record_gsyn()
populations[0].record()

p.run(500)

v = None
gsyn = None
spikes = None

v = populations[0].get_v(compatible_output=True)

current_file_path = os.path.dirname(os.path.abspath(__file__))
current_file_path = os.path.join(current_file_path, "v.data")
v_file = populations[0].print_v(current_file_path)


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

p.end()

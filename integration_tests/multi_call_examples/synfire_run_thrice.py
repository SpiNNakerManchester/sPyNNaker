"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p

def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)

    runtime = 1000
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

    projections.append(p.Projection(populations[0], populations[0],
                       p.FromListConnector(loopConnections)))
    projections.append(p.Projection(populations[1], populations[0],
                       p.FromListConnector(injectionConnection)))

    populations[0].record_v()
    populations[0].record_gsyn()
    populations[0].record()

    p.run(runtime)

    v1 = populations[0].get_v(compatible_output=True)
    gsyn1 = populations[0].get_gsyn(compatible_output=True)
    spikes1 = populations[0].getSpikes(compatible_output=True)

    p.run(runtime)

    v2 = populations[0].get_v(compatible_output=True)
    gsyn2 = populations[0].get_gsyn(compatible_output=True)
    spikes2 = populations[0].getSpikes(compatible_output=True)

    p.run(runtime)

    v3 = populations[0].get_v(compatible_output=True)
    gsyn3 = populations[0].get_gsyn(compatible_output=True)
    spikes3 = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v1, gsyn1, spikes1, v2, gsyn2, spikes2, v3, gsyn3, spikes3)

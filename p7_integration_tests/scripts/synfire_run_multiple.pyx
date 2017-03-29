"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p


def do_run(nNeurons, number_of_runs=1, reset=False, spike_times=[[0]]):
    """

    :param nNeurons: Number of Neurons in chain
    :type  nNeurons: int
    :param number_of_runs: Number of times run is called
    :type number_of_runs: int
    :param reset: if True will call reset before the additional runs
    :type reset: bool
    :param spike_times: times the inputer sends in spikes
    :type spike_times: matrix of int
    :return (v, gsyn, spikes)
        v: Volage after last run
        gysn: gysn after last run
        spikes: spikes after last run
    """
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
    spikeArray = {'spike_times': spike_times}
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

    for i in range(number_of_runs):
        p.run(runtime)
        if reset and i < number_of_runs - 1:
            p.reset()

    v = populations[0].get_v(compatible_output=True)
    gsyn = populations[0].get_gsyn(compatible_output=True)
    spikes = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v, gsyn, spikes)

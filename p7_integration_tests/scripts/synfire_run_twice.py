"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p


def do_run(nNeurons, second_run_multiple=1, reset=False, new_pop=False,
           modify_spike_array=False, extract_after_first=True):
    """

    :param nNeurons: Number of Neurons in chain
    :type  nNeurons: int
    :param second_run_multiple: Factor to adjust second run time
    :type second_run_multiple: float
    :param reset: if True will call reset before the second run
    :type reset: bool
    :param new_pop: If True will add a new population before the second run
    :type new_pop: bool
    :param modify_spike_array: If True will use a different spike array on the
        first pass and then change it to the standard (for this script)
        on the second run.
    :type modify_spike_array: bool
    :param extract_after_first: If True reads V1, gysn1 and spikes1
        between first and second run.
        Otherwise these three values will be returned as None
    :type extract_after_first: bool
    :return (v1, gsyn1, spikes1, v2, gsyn2, spikes2)
        v1: Volage after first run
        gysn1: gysn after first run
        spikes1: spikes after first run
        v2: Volage after second run
        gysn2: gysn after second run
        spikes2: spikes after second run
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
    if modify_spike_array:
        spikeArray = {'spike_times': [[0, 1050]]}
    else:
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

    if extract_after_first:
        v1 = populations[0].get_v(compatible_output=True)
        gsyn1 = populations[0].get_gsyn(compatible_output=True)
        spikes1 = populations[0].getSpikes(compatible_output=True)
    else:
        v1 = None
        gsyn1 = None
        spikes1 = None

    if new_pop:
        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_2'))
        injectionConnection = [(nNeurons - 1, 0, weight_to_spike, 1)]
        new_proj = p.Projection(populations[0], populations[2],
                                p.FromListConnector(injectionConnection))
        projections.append(new_proj)

    if modify_spike_array:
        modified_spike_array = [[0, 1050]]
        populations[1].tset("spike_times", modified_spike_array)

    if reset:
        p.reset()

    p.run(runtime * second_run_multiple)

    v2 = populations[0].get_v(compatible_output=True)
    gsyn2 = populations[0].get_gsyn(compatible_output=True)
    spikes2 = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v1, gsyn1, spikes1, v2, gsyn2, spikes2)

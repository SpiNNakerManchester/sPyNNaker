#!/usr/bin/python
"""
Synfirechain-like example
"""
import numpy

import spynnaker.pyNN as p


def do_run(nNeurons, n_pops, neurons_per_core, runtime=25000):
    """

    :param nNeurons: Number of Neurons in chain
    :type  nNeurons: int
    :param n_pops: Number of populations
    ;type n_pops: int
    :param neurons_per_core: Number of neurons per core
    :type neurons_per_core: int
    """
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", neurons_per_core)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 2.0
    delay = 1

    connections = list()
    for i in range(0, nNeurons - 1):
        singleConnection = (i, i + 1, weight_to_spike, delay)
        connections.append(singleConnection)

    pop_jump_connection = [(nNeurons - 1, 0, weight_to_spike, 1)]

    injectionConnection = [(0, 0, weight_to_spike, 1)]

    spikeArray = {'spike_times': [[0]]}

    for i in range(0, n_pops):
        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif,
                                        label='pop_{}'.format(i)))

    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    for i in range(0, n_pops):
        projections.append(p.Projection(populations[i], populations[i],
                                        p.FromListConnector(connections)))
        connector = p.FromListConnector(pop_jump_connection)
        projections.append(p.Projection(populations[i],
                                        populations[((i + 1) % n_pops)],
                                        connector))

    projections.append(p.Projection(populations[n_pops], populations[0],
                                    p.FromListConnector(injectionConnection)))

    for pop_index in range(0, n_pops):
        populations[pop_index].record()

    p.run(runtime)

    total_spikes = None
    total_spikes = populations[0].getSpikes(compatible_output=True)
    for pop_index in range(1, n_pops):
        spikes = populations[pop_index].getSpikes(compatible_output=True)
        if spikes is not None:
            for spike in spikes:
                spike[0] += (nNeurons * pop_index)
            total_spikes = numpy.concatenate((total_spikes, spikes), axis=0)

    p.end()

    return total_spikes

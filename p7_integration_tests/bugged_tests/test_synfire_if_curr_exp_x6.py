#!/usr/bin/python
"""
Synfirechain-like example with 6 chains
"""

from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.pyNN as p


def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", 100)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 10.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                       'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -64.4}

    populations = list()
    projections = list()

    weight_to_spike = 2
    delay = 1

    connections = list()
    for i in range(0, nNeurons):
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, delay)]
    spikeArray = {'spike_times': [[0]]}
    for x in range(6):
        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray))

    for x in range(0, 12, 2):
        projections.append(p.Projection(populations[x], populations[x],
                                        p.FromListConnector(connections)))
        connector = p.FromListConnector(injectionConnection)
        projections.append(p.Projection(populations[x+1], populations[x],
                                        connector))
        populations[x].record()

    p.run(1000)

    p.end()


class SynfireIfCurrx6(BaseTestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        do_run(nNeurons)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    do_run(nNeurons)

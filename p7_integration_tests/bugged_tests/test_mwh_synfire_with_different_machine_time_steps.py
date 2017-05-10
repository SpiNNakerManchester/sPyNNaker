#!/usr/bin/python
"""
Synfirechain-like example
"""

import spynnaker.pyNN as p
import spynnaker.plot_utils as plot_utils

from p7_integration_tests.base_test_case import BaseTestCase


def do_run(nNeurons):

    p.setup(timestep=0.1, min_delay=1.0, max_delay=7.5)
    p.set_number_of_neurons_per_core("IF_curr_exp", 100)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 6, 'tau_syn_I': 6,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -55.4}

    populations = list()
    projections = list()

    weight_to_spike = 12
    injection_delay = 1
    delay = 1

    spikeArray = {'spike_times': [[0, 10, 20, 30]]}
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='pop_0'))
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_2'))

    connector = p.AllToAllConnector(weights=weight_to_spike,
                                    delays=injection_delay)
    projections.append(p.Projection(populations[0], populations[1], connector))
    connector = p.OneToOneConnector(weights=weight_to_spike, delays=delay)
    projections.append(p.Projection(populations[1], populations[2], connector))

    populations[1].record_v()
    populations[1].record()

    p.run(100)

    v = populations[1].get_v(compatible_output=True)
    spikes = populations[1].getSpikes(compatible_output=True)

    p.end()

    return (v, spikes)


class MwhSynfireWithDifferentMachineTimeSteps(BaseTestCase):

    def test_run(self):
        nNeurons = 3  # number of neurons in each population
        (v, spikes) = do_run(nNeurons)
        self.assertLess(45, len(spikes))
        self.assertGreater(55, len(spikes))


if __name__ == '__main__':
    nNeurons = 3  # number of neurons in each population
    (v, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")

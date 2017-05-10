#!/usr/bin/python
"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.pyNN as p
import spynnaker.plot_utils as plot_utils


def do_run(nNeurons):
    p.setup(timestep=1, min_delay=1, max_delay=15)

    nNeurons = 1  # number of neurons in each population

    neuron_parameters = {'cm': 0.25, 'i_offset': 2, 'tau_m': 10.0,
                         'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                         'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()

    populations.append(p.Population(nNeurons, p.IF_curr_exp, neuron_parameters,
                                    label='pop_1'))
    populations.append(p.Population(nNeurons, p.IF_curr_exp, neuron_parameters,
                                    label='pop_2'))
    populations[1].add_placement_constraint(x=1, y=0)

    populations[0].record_v()
    populations[0].record_gsyn()
    populations[0].record()
    populations[1].record_v()
    populations[1].record_gsyn()
    populations[1].record()

    p.run(100)

    v1 = populations[0].get_v()
    gsyn1 = populations[0].get_gsyn()
    spikes1 = populations[0].getSpikes()
    v2 = populations[0].get_v()
    gsyn2 = populations[0].get_gsyn()
    spikes2 = populations[0].getSpikes()

    p.end()

    return (v1, gsyn1, v2, gsyn2, spikes1, spikes2)


class ATest(BaseTestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        (v1, gsyn1, v2, gsyn2, spikes1, spikes2) = do_run(nNeurons)
        self.assertLess(15, len(spikes1))
        self.assertGreater(25, len(spikes1))
        self.assertLess(15, len(spikes2))
        self.assertGreater(25, len(spikes2))


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    (v1, gsyn1, v2, gsyn2, spikes1, spikes2) = do_run(nNeurons)
    print len(spikes1)
    print len(spikes1)
    plot_utils.plot_spikes(spikes1, spikes2)
    plot_utils.heat_plot(v1, title="v1")
    plot_utils.heat_plot(v2, title="v2")
    plot_utils.heat_plot(gsyn1, title="gysn1")
    plot_utils.heat_plot(gsyn2, title="gysn2")

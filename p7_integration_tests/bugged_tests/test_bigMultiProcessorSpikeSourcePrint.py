"""
Synfirechain-like example
"""
# !/usr/bin/python
import spynnaker.pyNN as p

from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils


def do_run(nNeurons):
    cell_params_lif = {'cm': 0.25,  # nF
                       'i_offset': 0.0,
                       'tau_m': 10.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 2.5,
                       'tau_syn_I': 2.5,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -55.4
                       }

    spike_list = {'spike_times': [float(x) for x in range(0, 599, 50)]}
    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)

    p.set_number_of_neurons_per_core("SpikeSourceArray", 100)  # FAILS

    populations = list()
    projections = list()

    populations.append(p.Population(nNeurons, p.SpikeSourceArray, spike_list,
                                    label='input'))
    populations.append(p.Population(1, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))
    projections.append(p.Projection(populations[0], populations[1],
                                    p.AllToAllConnector()))

    populations[0].record()

    p.run(1000)

    spikes = populations[0].getSpikes(compatible_output=True)

    p.end()

    return spikes


class BigMultiProcessorSpikeSourcePrint(BaseTestCase):

    def test_run_(self):
        nNeurons = 600  # number of neurons in each population
        spikes = do_run(nNeurons)
        self.assertGreater(len(spikes), 7100)
        self.assertLess(len(spikes), 7300)


if __name__ == '__main__':
    nNeurons = 600  # number of neurons in each population
    spikes = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    print spikes

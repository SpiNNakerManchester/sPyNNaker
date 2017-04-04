#!/usr/bin/python
"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", 100)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 10.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                       'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -64.4}

    populations = list()
    projections = list()

    weight_to_spike = 2
    injection_delay = 2
    delay = 10

    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    connector = p.AllToAllConnector(weights=weight_to_spike, delays=delay)
    projections.append(p.Projection(populations[0], populations[0], connector))
    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector([(0, 0, 4,
                                                          injection_delay)])))

    populations[0].record_v()
    populations[0].record_gsyn()
    populations[0].record()

    p.run(90)

    v = populations[0].get_v(compatible_output=True)
    spikes = populations[0].getSpikes(compatible_output=True)
    gsyn = populations[0].get_gsyn(compatible_output=True)

    p.end()

    return (v, gsyn, spikes)


class ParamsSetAsList(BaseTestCase):

    # @unittest.skip("skipping test_bugged_tests/params_set_as_list")
    def test_run(self):
        nNeurons = 2  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        self.assertLess(15, len(spikes))
        self.assertGreater(20, len(spikes))


if __name__ == '__main__':
    nNeurons = 2  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

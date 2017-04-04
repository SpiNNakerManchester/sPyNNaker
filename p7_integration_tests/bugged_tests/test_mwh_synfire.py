#!/usr/bin/python
"""
Synfirechain-like example
"""
import spynnaker.pyNN as p
from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core("IF_curr_exp", 250)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 5.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 1.5
    delay = 1

    connections = list()
    for i in range(0, nNeurons):
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, delay)]

    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    projections.append(p.Projection(populations[0], populations[0],
                                    p.FromListConnector(connections)))
    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector(injectionConnection)))

    populations[0].record_v()
    populations[0].record_gsyn()
    populations[0].record()

    p.run(1000)

    ''''
    weights = projections[0].getWeights()
    delays = projections[0].getDelays()
    '''

    v = populations[0].get_v(compatible_output=True)
    gsyn = populations[0].get_gsyn(compatible_output=True)
    spikes = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v, gsyn, spikes)


class MwhSynfire(BaseTestCase):
    def test_run(self):
        nNeurons = 100  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        # plot_utils.plot_spikes(spikes)
        # plot_utils.heat_plot(v, title="v")
        # plot_utils.heat_plot(gsyn, title="gysn")
        # print len(spikes)
        self.assertLess(180, len(spikes))
        self.assertGreater(220, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 100  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

#!/usr/bin/python
"""
Synfirechain-like example
"""
import numpy
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.pyNN as p
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker


def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    max_delay = 50
    p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 2.0
    delay = numpy.random.RandomState()
    delays = list()

    connections = list()
    for i in range(0, nNeurons):
        d_value = int(delay.uniform(low=1, high=max_delay))
        delays.append(float(d_value))
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, d_value)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, 1)]
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

    run_time = (max_delay * nNeurons)
    print "Running for {} ms".format(run_time)
    p.run(run_time)

    v = populations[0].get_v(compatible_output=True)
    gsyn = populations[0].get_gsyn(compatible_output=True)
    spikes = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v, gsyn, spikes)


class SynfireIfCurrExpRandom(BaseTestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p

import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
    nNeurons = 200  # number of neurons in each population
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
    spikeArray = {'spike_times': [[0, 1050]]}
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

    v1 = populations[0].get_v(compatible_output=True)
    gsyn1 = populations[0].get_gsyn(compatible_output=True)
    spikes1 = populations[0].getSpikes(compatible_output=True)

    p.run(runtime / 2)

    v2 = populations[0].get_v(compatible_output=True)
    gsyn2 = populations[0].get_gsyn(compatible_output=True)
    spikes2 = populations[0].getSpikes(compatible_output=True)

    p.end()

    return (v1, gsyn1, spikes1, v2, gsyn2, spikes2)


class Synfire2RunExtractionIfCurrExpLowerSecondRun(unittest.TestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        (v1, gsyn1, spikes1, v2, gsyn2, spikes2) = do_run(nNeurons)
        # print len(spikes1)
        # print len(spikes2)
        # plot_utils.plot_spikes(spikes1, spikes2)
        # plot_utils.heat_plot(v1, title="v1")
        # plot_utils.heat_plot(gsyn1, title="gysn1")
        # plot_utils.heat_plot(v2, title="v2")
        # plot_utils.heat_plot(gsyn2, title="gysn2")
        self.assertEquals(53, len(spikes1))
        self.assertEquals(103, len(spikes2))
        spike_checker.synfire_spike_checker(spikes1, nNeurons)
        spike_checker.synfire_multiple_lines_spike_checker(spikes2, nNeurons, 2)

if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    (v1, gsyn1, spikes1, v2, gsyn2, spikes2) = do_run(nNeurons)
    print len(spikes1)
    print len(spikes2)
    plot_utils.plot_spikes(spikes1, spikes2)
    plot_utils.heat_plot(v1, title="v1")
    plot_utils.heat_plot(gsyn1, title="gysn1")
    plot_utils.heat_plot(v2, title="v2")
    plot_utils.heat_plot(gsyn2, title="gysn2")
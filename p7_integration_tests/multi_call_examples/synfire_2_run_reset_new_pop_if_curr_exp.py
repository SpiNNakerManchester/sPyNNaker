"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run_multiple as \
    synfire_run_multiple


class Synfire1RunResetNewPopIfCurrExp(unittest.TestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = synfire_run_multiple.do_run(nNeurons,  number_of_runs=2,
                                              reset=True)
        (v, gsyn, spikes) = results
        # print len(spikes)
        # plot_utils.plot_spikes(spikes)
        # plot_utils.heat_plot(v, title="v")
        # plot_utils.heat_plot(gsyn, title="gysn")
        self.assertEquals(53, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run_multiple.do_run(nNeurons, number_of_runs=2,
                                          reset=True)
    (v, gsyn, spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gysn")

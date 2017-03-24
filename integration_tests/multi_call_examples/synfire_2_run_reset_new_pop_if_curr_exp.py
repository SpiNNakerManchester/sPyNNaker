"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import synfire_run_twice as synfire_run_twice

class Synfire1RunResetNewPopIfCurrExp(unittest.TestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = synfire_run_twice.do_run(nNeurons, reset=True, new_pop=True,
                                           extract_after_first=False)
        (v1, gsyn1, spikes1, v2, gsyn2, spikes2) = results
        # print len(spikes2)
        # plot_utils.plot_spikes(spikes2)
        # plot_utils.heat_plot(v2, title="v2")
        # plot_utils.heat_plot(gsyn2, title="gysn2")
        self.assertIsNone(v1)
        self.assertIsNone(gsyn1)
        self.assertIsNone(spikes1)
        self.assertEquals(53, len(spikes2))
        spike_checker.synfire_spike_checker(spikes2, nNeurons)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run_twice.do_run(nNeurons, reset=True, new_pop=True,
                                       extract_after_first=False)
    (v1, gsyn1, spikes1, v2, gsyn2, spikes2) = results
    print len(spikes2)
    plot_utils.plot_spikes(spikes2)
    plot_utils.heat_plot(v2, title="v2")
    plot_utils.heat_plot(gsyn2, title="gysn2")
"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run_multiple as \
    synfire_run_multiple


SPIKE_TIMES = [[1050, 1060, 1500, 1700, 1900, 2200]]

class Synfire3RunNoSpikesInFirstExitNoExtractionIfCurrExp(unittest.TestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = synfire_run_multiple.do_run(nNeurons,  number_of_runs=3,
                                              spike_times=SPIKE_TIMES )
        (v, gsyn, spikes) = results
        self.assertEquals(454, len(spikes))
        spike_checker.synfire_multiple_lines_spike_checker(spikes, nNeurons, 6)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run_multiple.do_run(nNeurons,  number_of_runs=3,
                                          spike_times=SPIKE_TIMES )
    (v, gsyn, spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gysn")



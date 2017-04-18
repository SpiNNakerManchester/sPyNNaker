"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run as synfire_run


class Synfire3RunNoSpikesInFirstExitNoExtractionIfCurrExp(BaseTestCase):
    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = synfire_run.do_run(nNeurons, spike_times=[[1050, 2200]],
                                     run_times=[1000, 1000, 1000], reset=False,
                                     extract_between_runs=False)
        (v, gsyn, spikes, inpur_spikes) = results
        self.assertEquals(145, len(spikes))
        spike_checker.synfire_multiple_lines_spike_checker(spikes, nNeurons, 2)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run.do_run(nNeurons, spike_times=[[1050, 2200]],
                                 run_times=[1000, 1000, 1000], reset=False,
                                 extract_between_runs=False)
    (v, gsyn, spikes, inpur_spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gysn")

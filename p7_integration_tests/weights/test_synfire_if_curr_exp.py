"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run as synfire_run


class SynfireIfCurr_exp(BaseTestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = synfire_run.do_run(nNeurons, neurons_per_core=10, delay=17,
                                     run_times=[5000], get_weights=True)
        (v, gsyn, spikes, weights) = results
        self.assertEquals(263, len(spikes))
        self.assertEquals(200, len(weights))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run.do_run(nNeurons, neurons_per_core=10, delay=17,
                                 run_times=[5000], get_weights=True)
    (v, gsyn, spikes, weights) = results
    print len(spikes)
    print len(weights)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v)
    plot_utils.heat_plot(gsyn)

#!/usr/bin/python
"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils

import p7_integration_tests.scripts.synfire_npop_run as synfire_npop_run

n_neurons = 10  # number of neurons in each population
n_pops = 630


class Synfire6300n10pop10pc48chipsNoDelaysSpikeRecording(BaseTestCase):

    def test_run(self):
        results = synfire_npop_run.do_run(n_neurons, n_pops=n_pops,
                                          neurons_per_core=n_neurons)
        spikes = results
        self.assertEquals(8333, len(spikes))


if __name__ == '__main__':
    results = synfire_npop_run.do_run(n_neurons, n_pops=n_pops,
                                      neurons_per_core=n_neurons)
    spikes = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)

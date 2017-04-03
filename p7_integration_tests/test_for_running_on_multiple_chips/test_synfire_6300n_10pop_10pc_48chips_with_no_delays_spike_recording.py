#!/usr/bin/python
"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_npop_run as synfire_npop_run

n_neurons = 10  # number of neurons in each population
n_pops=630

class Synfire6300n10pop10pc48chipsNoDelaysSpikeRecording(unittest.TestCase):

    def test_run(self):
        results = synfire_npop_run.do_run(n_neurons, n_pops=n_pops,
                                          neurons_per_core=n_neurons)
        spikes = results
        self.assertEquals(8333, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)


if __name__ == '__main__':
    results = synfire_npop_run.do_run(n_neurons, n_pops=n_pops,
                                      neurons_per_core=n_neurons)
    spikes = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)

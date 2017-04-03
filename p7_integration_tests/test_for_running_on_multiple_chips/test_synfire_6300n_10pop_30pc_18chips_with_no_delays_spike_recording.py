#!/usr/bin/python
"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_npop_run as synfire_npop_run


class Synfire6300n10pop30pc18chipsNoDelaysSpikeRrecording(unittest.TestCase):

    def test_run(self):
        nNeurons = 630  # number of neurons in each population
        results = synfire_npop_run.do_run(nNeurons, n_pops=10,
                                          neurons_per_core=30)
        spikes = results
        self.assertEquals(8333, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 10  # number of neurons in each population
    results = synfire_npop_run.do_run(nNeurons, n_pops=630)
    spikes = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)

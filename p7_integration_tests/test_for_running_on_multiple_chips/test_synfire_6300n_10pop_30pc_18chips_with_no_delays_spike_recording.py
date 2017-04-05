#!/usr/bin/python
"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_npop_run as synfire_npop_run

nNeurons = 630  # number of neurons in each population
runtime = 5000
n_pops = 10
neurons_per_core = 30


class Synfire6300n10pop30pc18chipsNoDelaysSpikeRrecording(BaseTestCase):

    def test_run(self):
        results = synfire_npop_run.do_run(nNeurons, n_pops=n_pops,
                                          neurons_per_core=neurons_per_core,
                                          runtime=runtime)
        spikes = results
        self.assertEquals(1666, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons * n_pops)


if __name__ == '__main__':
    nNeurons = 10  # number of neurons in each population
    results = synfire_npop_run.do_run(nNeurons, n_pops=n_pops,
                                      neurons_per_core=neurons_per_core,
                                      runtime=runtime)
    spikes = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)

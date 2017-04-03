#!/usr/bin/python
"""
Synfirechain-like example
"""
import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run as synfire_run

nNeurons = 200  # number of neurons in each population
delay = 1
neurons_per_core = 50


class Synfire200n50pc4cWithNoDelaysSpikeRecording(unittest.TestCase):

    def test_run(self):
        results = synfire_run.do_run(nNeurons, delay=delay,
                                     neurons_per_core=neurons_per_core,
                                     record_v=False, record_gsyn=False)
        (v, gsyn, spikes) = results
        self.assertEquals(333, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    results = synfire_run.do_run(nNeurons, delay=delay,
                                 neurons_per_core=neurons_per_core,
                                 record_v=False, record_gsyn=False)
    (v, gsyn, spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    # v and gysn are None

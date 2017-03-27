"""
Synfirechain-like example
"""
#!/usr/bin/python

import unittest

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run as synfire_run


class Synfire1600n10pc10chipsWithNoDelaysSpikeRecording(unittest.TestCase):

    def test_run(self):
        nNeurons = 1600  # number of neurons in each population
        results = synfire_run.do_run(nNeurons, runtime=5000,
                                     record_v=False, record_gsyn=False)
        (v, gsyn, spikes) = results
        self.assertEquals(263, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 1600  # number of neurons in each population
    results = synfire_run.do_run(nNeurons, runtime=5000, record_v=False,
                                 record_gsyn=False)
    (v, gsyn, spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    # v and gysn are None


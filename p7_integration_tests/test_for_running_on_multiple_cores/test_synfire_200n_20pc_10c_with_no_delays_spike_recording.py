#!/usr/bin/python
"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

import p7_integration_tests.scripts.synfire_run as synfire_run


class Synfire200n20pc10cWithNoDelaysSpikeRecording(BaseTestCase):

    def test_run(self):
        nNeurons = 200  # number of neurons in each population
        results = synfire_run.do_run(nNeurons,  delay=1, neurons_per_core=20,
                                     record_v=False, record_gsyn=False)
        (v, gsyn, spikes, inpur_spikes) = results
        self.assertEquals(333, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    results = synfire_run.do_run(nNeurons, delay=1, neurons_per_core=20,
                                 record_v=False, record_gsyn=False)
    (v, gsyn, spikes, inpur_spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    # v and gysn are None

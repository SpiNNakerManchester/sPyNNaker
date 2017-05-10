#!/usr/bin/python
"""
Synfirechain-like example
"""

from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

nNeurons = 1600  # number of neurons in each population
run_times = [5000]
record_v = False
record_gsyn = False
synfire_run = TestRun()


class Synfire1600n10pc10chipsWithNoDelaysSpikeRecording(BaseTestCase):

    def test_run(self):
        synfire_run.do_run(nNeurons, run_times=run_times, record_v=record_v,
                           record_gsyn=record_gsyn)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(263, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, run_times=run_times, record_v=record_v,
                       record_gsyn=record_gsyn)
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes)
    plot_utils.plot_spikes(spikes)
    # v and gysn are None

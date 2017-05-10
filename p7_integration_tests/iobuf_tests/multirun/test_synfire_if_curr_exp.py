"""
Synfirechain-like example
"""
import unittest
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

n_neurons = 200  # number of neurons in each population
runtimes = [1000, 1000, 1000, 1000, 1000]
neurons_per_core = n_neurons / 2
synfire_run = TestRun()


class SynfireIfCurrExp(BaseTestCase):

    @unittest.skip("skipping test_buffer_manager/if_curr_exp_live_buiffer/"
                   "SynfireIfCurrExp")
    def test_run(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=runtimes, record=False, record_v=False,
                           record_gsyn=False)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(158, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        print len(spikes)
        self.assertGreater(len(spikes), 100)
        self.assertLess(len(spikes), 200)
        spike_checker.synfire_spike_checker(spikes, n_neurons)


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 run_times=runtimes, record=False,
                                 record_v=False, record_gsyn=False)
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    (v, gsyn, spikes, inpur_spikes) = results
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

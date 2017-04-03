"""
Synfirechain-like example
"""
import unittest
import p7_integration_tests.scripts.synfire_run as synfire_run
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

n_neurons = 200  # number of neurons in each population
runtime = 5000
neurons_per_core = n_neurons / 2


class SynfireIfCurrExp(unittest.TestCase):

    @unittest.skip("skipping test_buffer_manager/if_curr_exp_live_buiffer/"
                   "SynfireIfCurrExp")
    def test_run(self):
        results = synfire_run.do_run(n_neurons,
                                     neurons_per_core=neurons_per_core,
                                     runtimes=[runtime])
        (v, gsyn, spikes) = results
        self.assertEquals(158, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        print len(spikes)
        self.assertGreater(len(spikes), 100)
        self.assertLess(len(spikes), 200)
        spike_checker.synfire_spike_checker(spikes, n_neurons)


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 runtimes=[runtime])
    (v, gsyn, spikes) = results
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

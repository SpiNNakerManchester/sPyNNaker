"""
Synfirechain-like example
"""
import unittest
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run

n_neurons = 200  # number of neurons in each population
runtimes = [5000]
neurons_per_core = n_neurons / 2


class SynfireIfCurrExp(BaseTestCase):

    @unittest.skip("skipping test_buffer_manager/if_curr_exp_live_buiffer/"
                   "SynfireIfCurrExp")
    def test_run(self):
        results = synfire_run.do_run(n_neurons,
                                     neurons_per_core=neurons_per_core,
                                     runtimes=runtimes, record=False,
                                     record_v=False, record_gsyn=False)
        (v, gsyn, spikes) = results


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 runtimes=runtimes, record=False,
                                 record_v=False, record_gsyn=False)
    (v, gsyn, spikes) = results

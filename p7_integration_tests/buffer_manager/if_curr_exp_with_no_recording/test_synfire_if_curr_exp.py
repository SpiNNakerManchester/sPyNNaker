"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run

n_neurons = 200  # number of neurons in each population
runtime = 5000
neurons_per_core = n_neurons / 2
record = False
record_v = False
record_gsyn = False


class SynfireIfCurrExp(BaseTestCase):

    def test_run(self):
        results = synfire_run.do_run(n_neurons,
                                     neurons_per_core=neurons_per_core,
                                     runtimes=[runtime], record=record,
                                     record_v=record_v,
                                     record_gsyn=record_gsyn,
                                     )
        (v, gsyn, spikes) = results
        self.assertIsNone(v)
        self.assertIsNone(gsyn)
        self.assertIsNone(spikes)


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 runtimes=[runtime], record=record,
                                 record_v=record_v, record_gsyn=record_gsyn, )
    (v, gsyn, spikes) = results

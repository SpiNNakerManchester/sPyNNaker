"""
Synfirechain-like example
"""
try:
    import pyNN.spiNNaker as p
except Exception as e:
    import spynnaker.pyNN as p

import unittest
import p7_integration_tests.scripts.synfire_run as synfire_run
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

n_neurons = 200  # number of neurons in each population
runtime = 5000
neurons_per_core = n_neurons / 2
record = False
record_v = True
record_gsyn = False


class SynfireIfCurrExp(unittest.TestCase):

    def test_run(self):
        results = synfire_run.do_run(n_neurons,
                                     neurons_per_core=neurons_per_core,
                                     runtimes=[runtime], record=record,
                                     record_v=record_v, record_gsyn=record_gsyn,
                                     )
        (v, gsyn, spikes) = results
        self.assertIsNone(gsyn)
        self.assertIsNone(spikes)

if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 runtimes=[runtime], record=record,
                                 record_v=record_v, record_gsyn=record_gsyn, )
    (v, gsyn, spikes) = results
    plot_utils.line_plot(v, title="v")



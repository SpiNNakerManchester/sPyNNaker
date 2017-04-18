"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun
import spynnaker.plot_utils as plot_utils

n_neurons = 200  # number of neurons in each population
runtime = 5000
neurons_per_core = n_neurons / 2
record = False
record_v = True
record_gsyn = False
synfire_run = TestRun()


class SynfireIfCurrExp(BaseTestCase):

    def test_run(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=[runtime], record=record,
                           record_v=record_v, record_gsyn=record_gsyn)
        gsyn = synfire_run.get_output_pop_gsyn()
        v = synfire_run.get_output_pop_voltage()
        spikes = synfire_run.get_output_pop_spikes()

        self.assertIsNone(gsyn)
        self.assertIsNone(v)
        self.assertIsNone(spikes)


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=[runtime], record=record, record_v=record_v,
                       record_gsyn=record_gsyn)
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    plot_utils.line_plot(v, title="v")

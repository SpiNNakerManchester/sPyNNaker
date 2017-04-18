"""
Synfirechain-like example
"""
# general imports
from p7_integration_tests.scripts.synfire_run import TestRun
from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
import spynnaker.gsyn_tools as gsyn_tools
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest

n_neurons = 10  # number of neurons in each population
runtime = 50
synfire_run = TestRun()


class TestGsyn(BaseTestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_get_gsyn(self):
        try:
            synfire_run.do_run(
                n_neurons, max_delay=14.4, time_step=0.1,
                neurons_per_core=5, delay=1.7, run_times=[runtime])

            spikes = synfire_run.get_output_pop_spikes()
            # no check of spikes length as the system overloads
            spike_checker.synfire_spike_checker(spikes, n_neurons)
            # no check of gsyn as the system overloads
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest(ex)


if __name__ == '__main__':
    synfire_run.do_run(
        n_neurons, max_delay=14.4, time_step=0.1, neurons_per_core=5,
        delay=1.7, run_times=[runtime])
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v)
    plot_utils.heat_plot(gsyn)
    gsyn_tools.check_sister_gysn(__file__, n_neurons, runtime, gsyn)

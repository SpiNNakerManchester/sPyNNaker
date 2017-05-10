"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker


n_neurons = 200  # number of neurons in each population
neurons_per_core = n_neurons / 2
spike_times = [[0, 1050]]
runtimes = [1000, 500]
reset = False
synfire_run = TestRun()


class Synfire2RunExtractionIfCurrExpLowerSecondRun(BaseTestCase):
    def test_run(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           spike_times=spike_times, run_times=runtimes,
                           reset=reset)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(53, len(spikes[0]))
        self.assertEquals(103, len(spikes[1]))
        spike_checker.synfire_spike_checker(spikes[0], n_neurons)
        spike_checker.synfire_multiple_lines_spike_checker(spikes[1],
                                                           n_neurons, 2)


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 spike_times=spike_times, run_times=runtimes,
                                 reset=reset)\

    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes[0])
    print len(spikes[1])
    plot_utils.plot_spikes(spikes[0], spikes[1])
    plot_utils.heat_plot(v[0], title="v1")
    plot_utils.heat_plot(gsyn[0], title="gysn1")
    plot_utils.heat_plot(v[1], title="v2")
    plot_utils.heat_plot(gsyn[1], title="gysn2")

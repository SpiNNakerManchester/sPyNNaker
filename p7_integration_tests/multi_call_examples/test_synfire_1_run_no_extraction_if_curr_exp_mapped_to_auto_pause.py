"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
import p7_integration_tests.scripts.synfire_run as synfire_run

n_neurons = 200  # number of neurons in each population
neurons_per_core = n_neurons / 2
runtimes = [526, 526, 526, 526, 526, 370]
extract_between_runs=False

class Synfire1RunNoExtractionIfCurrExpMappedToAutoPause(BaseTestCase):

    def test_run(self):
        results = synfire_run.do_run(n_neurons,
                                     neurons_per_core=neurons_per_core,
                                     runtimes=runtimes,
                                     extract_between_runs=extract_between_runs)
        (v, gsyn, spikes) = results
        self.assertEqual(158, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                                 runtimes=runtimes,
                                 extract_between_runs=extract_between_runs)
    (v, gsyn, spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

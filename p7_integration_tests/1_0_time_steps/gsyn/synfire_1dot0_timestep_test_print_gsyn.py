"""
Synfirechain-like example
"""

# spynnaker imports
import os
from p7_integration_tests.base_test_case import BaseTestCase
import p7_integration_tests.scripts.synfire_run as synfire_run
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
import spynnaker.gsyn_tools as gsyn_tools


n_neurons = 10  # number of neurons in each population
max_delay = 14.4
timestep = 1
neurons_per_core = n_neurons/2
delay = 1.7
runtime = 50
gsyn_path = os.path.dirname(os.path.abspath(__file__))
gsyn_path = os.path.join(gsyn_path, "gsyn.data2")


class TestPrintGsyn(BaseTestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_get_gsyn(self):
        results = synfire_run.do_run(n_neurons, max_delay=max_delay,
                                     time_step=timestep,
                                     neurons_per_core=neurons_per_core,
                                     delay=delay,
                                     run_times=[runtime], gsyn_path=gsyn_path)
        (v, gsyn, spikes, inpur_spikes) = results
        self.assertEquals(56, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        gsyn_tools.check_path_gysn(gsyn_path, n_neurons, runtime, gsyn)
        os.remove(gsyn_path)


if __name__ == '__main__':
    results = synfire_run.do_run(n_neurons, max_delay=max_delay,
                                 time_step=timestep,
                                 neurons_per_core=neurons_per_core,
                                 delay=delay,
                                 run_times=[runtime], gsyn_path=gsyn_path)
    (v, gsyn, spikes, inpur_spikes) = results
    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v)
    plot_utils.heat_plot(gsyn)
    gsyn_tools.check_sister_gysn(__file__, n_neurons, runtime, gsyn)
    # os.remove(gsyn_path)

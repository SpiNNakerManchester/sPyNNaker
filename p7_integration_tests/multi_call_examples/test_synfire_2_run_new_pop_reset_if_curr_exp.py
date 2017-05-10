"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

nNeurons = 200  # number of neurons in each population
spike_times = [[0, 1050]]
run_times = [1000, 1000]
reset = True
new_pop = True
synfire_run = TestRun()


class Synfire1RunReset1RunNo_extraction_if_curr_exp(BaseTestCase):
    def test_run(self):
        synfire_run.do_run(nNeurons, spike_times=spike_times,
                           run_times=run_times, reset=reset, new_pop=new_pop)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(53, len(spikes[0]))
        self.assertEquals(53, len(spikes[1]))
        spike_checker.synfire_spike_checker(spikes[0], nNeurons)
        spike_checker.synfire_spike_checker(spikes[1], nNeurons)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, spike_times=spike_times, run_times=run_times,
                       reset=reset, new_pop=new_pop)
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

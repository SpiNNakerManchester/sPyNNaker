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
extract_between_runs = False
reset = True
new_pop = True
synfire_run = TestRun()


class Synfire2RunResetFileWriteIssue(BaseTestCase):
    def test_run(self):
        synfire_run.do_run(nNeurons, spike_times=spike_times,
                           run_times=run_times,
                           extract_between_runs=extract_between_runs,
                           reset=reset, new_pop=new_pop)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(53, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, spike_times=spike_times, run_times=run_times,
                       extract_between_runs=extract_between_runs, reset=reset,
                       new_pop=new_pop)
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gysn")

"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

nNeurons = 200  # number of neurons in each population
SPIKE_TIMES = [[1050, 1060, 1500, 1700, 1900, 2200]]
run_times = [1000, 1000, 1000]
reset = False
extract_between_runs = False
synfire_run = TestRun()


class Synfire3RunNoSpikesInFirstExitNoExtractionIfCurrExp(BaseTestCase):
    def test_run(self):
        synfire_run.do_run(nNeurons, spike_times=SPIKE_TIMES,
                           run_times=run_times, reset=reset,
                           extract_between_runs=extract_between_runs)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(454, len(spikes))
        spike_checker.synfire_multiple_lines_spike_checker(spikes, nNeurons, 6)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, spike_times=SPIKE_TIMES, run_times=run_times,
                       reset=reset, extract_between_runs=extract_between_runs)
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gysn")

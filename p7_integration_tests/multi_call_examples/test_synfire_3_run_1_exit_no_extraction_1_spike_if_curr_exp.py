"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker

nNeurons = 200  # number of neurons in each population
run_times = [1000, 1000, 1000]
extract_between_runs = False
reset = False
synfire_run = TestRun()


class Ssynfire3Run1ExitNoExtraction1SpikeIfCurrExp(BaseTestCase):
    def test_run(self):
        synfire_run.do_run(nNeurons, run_times=run_times,
                           extract_between_runs=extract_between_runs,
                           reset=reset)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(158, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, run_times=run_times,
                       extract_between_runs=extract_between_runs, reset=reset)
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gysn")

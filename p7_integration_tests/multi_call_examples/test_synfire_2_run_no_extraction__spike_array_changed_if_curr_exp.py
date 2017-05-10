"""
Synfirechain-like example
"""
from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker


nNeurons = 200  # number of neurons in each population
spike_times_list = [[[0]], [[0, 1050]]]
run_times = [1000, 1000]
synfire_run = TestRun()


class Synfire2RunNoExtractionSpikeArrayChanged(BaseTestCase):
    def test_run(self):
        synfire_run.do_run(nNeurons, spike_times_list=spike_times_list,
                           run_times=run_times)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(53, len(spikes[0]))
        self.assertEquals(156, len(spikes[1]))
        spike_checker.synfire_spike_checker(spikes[0], nNeurons)
        spike_checker.synfire_multiple_lines_spike_checker(spikes[1], nNeurons,
                                                           2)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, spike_times_list=spike_times_list,
                       run_times=run_times)
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

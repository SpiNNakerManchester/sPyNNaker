#!/usr/bin/python
"""
Synfirechain-like example
"""
import unittest
import numpy
import os.path
import spynnaker.spike_checker as spike_checker
import spynnaker.plot_utils as plot_utils

from p7_integration_tests.base_test_case import BaseTestCase
from p7_integration_tests.scripts.synfire_run import TestRun

n_neurons = 20  # number of neurons in each population
delay = 7
runtime = 200
neurons_per_core = None
placement_constraint = (0, 0, 2)
current_file_path = os.path.dirname(os.path.abspath(__file__))
spike_file = os.path.join(current_file_path, "20_7_spikes.csv")
v_file = os.path.join(current_file_path, "20_7_v.csv")
gysn_file = os.path.join(current_file_path, "20_7_gsyn.csv")


class Synfire20n20pcDelaysDelayExtensionsAllRecording(BaseTestCase):
    def test_all_no_constarint(self):
        synfire_run = TestRun()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime],
                           record=True, record_v=True, record_gsyn=True)
        gsyn = synfire_run.get_output_pop_gsyn()
        v = synfire_run.get_output_pop_voltage()
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(n_neurons*runtime, len(gsyn))
        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_gsyn, gsyn))

        self.assertEquals(n_neurons*runtime, len(v))
        read_v = numpy.loadtxt(v_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_v, v))

        self.assertEquals(22, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        read_spikes = numpy.loadtxt(spike_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_spikes, spikes))

    def test_spikes_no_constarint(self):
        synfire_run = TestRun()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime],
                           record=True, record_v=False, record_gsyn=False)
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(22, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        read_spikes = numpy.loadtxt(spike_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_spikes, spikes))

    def test_v_no_constarint(self):
        synfire_run = TestRun()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime],
                           record=False, record_v=True, record_gsyn=False)
        v = synfire_run.get_output_pop_voltage()

        self.assertEquals(n_neurons*runtime, len(v))
        read_v = numpy.loadtxt(v_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_v, v))

    def test_gsyn_no_constarint(self):
        synfire_run = TestRun()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime],
                           record=False, record_v=False, record_gsyn=True)
        gsyn = synfire_run.get_output_pop_gsyn()

        self.assertEquals(n_neurons*runtime, len(gsyn))
        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_gsyn, gsyn))

    @unittest.skip("/p7_integration_tests/"
                   "tests_for_param_vertex_retrieval_from_board_after_1_run/"
                   "synfire_20n_20pc_delays_delay_extensions_all_recording.py")
    def test_with_constarint(self):
        synfire_run = TestRun()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           placement_constraint=placement_constraint,
                           run_times=[runtime],
                           record=True, record_v=True, record_gsyn=True)
        gsyn = synfire_run.get_output_pop_gsyn()
        v = synfire_run.get_output_pop_voltage()
        spikes = synfire_run.get_output_pop_spikes()

        self.assertEquals(n_neurons*runtime, len(gsyn))
        self.assertEquals(n_neurons*runtime, len(v))
        self.assertEquals(27, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)


if __name__ == '__main__':
    synfire_run = TestRun()
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       delay=delay, run_times=[runtime],
                       record=True, record_v=True, record_gsyn=True)
    # placement_constraint BROKEN!
    # synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
    #                   placement_constraint=placement_constraint,
    #                   run_times=[runtime],
    #                   record=True, record_v=True, record_gsyn=True)
    gsyn = synfire_run.get_output_pop_gsyn()
    v = synfire_run.get_output_pop_voltage()
    spikes = synfire_run.get_output_pop_spikes()

    print len(spikes)
    plot_utils.plot_spikes(spikes)
    numpy.savetxt(spike_file, spikes, delimiter=',')

    plot_utils.heat_plot(v)
    numpy.savetxt(v_file, v, delimiter=',')

    plot_utils.heat_plot(gsyn)
    numpy.savetxt(gysn_file, gsyn, delimiter=',')

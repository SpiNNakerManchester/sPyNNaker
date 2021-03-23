#!/usr/bin/python

# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Synfirechain-like example
"""
import matplotlib.pyplot as plt
import numpy
from pyNN.utility.plotting import Figure
import spynnaker.spike_checker as spike_checker
from spynnaker.spynnaker_plotting import SpynnakerPanel
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 20  # number of neurons in each population
delay = 17
runtime = 500
neurons_per_core = None
placement_constraint = (0, 0)
expected_spikes = 27
spike_file = "20_17_spikes.csv"
v_file = "20_17_v.csv"
gysn_file = "20_17_gsyn.csv"


class Synfire20n20pcDelaysDelayExtensionsAllRecording(BaseTestCase):

    def do_all_no_constraint(self):
        synfire_run = SynfireRunner()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime], record=True,
                           record_7=True, record_v=True, record_v_7=True,
                           record_gsyn_exc=True, record_gsyn_exc_7=True,
                           record_gsyn_inh=False)
        gsyn_exc_7 = synfire_run.get_output_pop_gsyn_exc_7()
        v_7 = synfire_run.get_output_pop_voltage_7()
        spikes_7 = synfire_run.get_output_pop_spikes_7()

        gsyn_exc = synfire_run.get_output_pop_gsyn_exc_numpy()
        v = synfire_run.get_output_pop_voltage_numpy()
        spikes = synfire_run.get_output_pop_spikes_numpy()

        self.assertEqual(n_neurons*runtime, len(gsyn_exc))
        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_gsyn, gsyn_exc_7, rtol=1e-04),
                        "gsyn synakker method mismatch")
        self.assertTrue(numpy.allclose(read_gsyn, gsyn_exc, rtol=1e-04),
                        "gsyn neo method mismatch")

        self.assertEqual(n_neurons*runtime, len(v))
        read_v = numpy.loadtxt(v_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_v, v_7, rtol=1e-03),
                        "v synakker method mismatch")
        self.assertTrue(numpy.allclose(read_v, v, rtol=1e-03),
                        "v neo method mismatch")

        self.assertEqual(expected_spikes, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        read_spikes = numpy.loadtxt(spike_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_spikes, spikes_7),
                        "spikes synakker method mismatch")
        self.assertTrue(numpy.allclose(read_spikes, spikes),
                        "spikes neo method mismatch")

    def test_all_no_constraint(self):
        self.runsafe(self.do_all_no_constraint)

    def do_sampling_rate(self):
        synfire_run = SynfireRunner()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime], record=True,
                           record_7=True, record_v=True, record_v_7=True,
                           v_sampling_rate=2, gsyn_exc_sampling_rate=3,
                           record_gsyn_exc=True, record_gsyn_exc_7=True,
                           record_gsyn_inh=False)
        gsyn_exc_7 = synfire_run.get_output_pop_gsyn_exc_7()
        v_7 = synfire_run.get_output_pop_voltage_7()
        spikes_7 = synfire_run.get_output_pop_spikes_7()

        gsyn_exc = synfire_run.get_output_pop_gsyn_exc_numpy()
        v = synfire_run.get_output_pop_voltage_numpy()
        spikes = synfire_run.get_output_pop_spikes_numpy()

        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        small_gsyn = read_gsyn[read_gsyn[:, 1] % 3 == 0]
        self.assertEqual(len(small_gsyn), len(gsyn_exc_7))
        self.assertTrue(numpy.allclose(small_gsyn, gsyn_exc_7, rtol=1e-04),
                        "gsyn synakker method mismatch")
        self.assertTrue(numpy.allclose(small_gsyn, gsyn_exc, rtol=1e-04),
                        "gsyn neo method mismatch")

        self.assertEqual(n_neurons*(runtime/2), len(v))
        read_v = numpy.loadtxt(v_file, delimiter=',')
        small_v = read_v[read_v[:, 1] % 2 == 0]
        self.assertTrue(numpy.allclose(small_v, v_7, rtol=1e-03),
                        "v synakker method mismatch")
        self.assertTrue(numpy.allclose(small_v, v, rtol=1e-03),
                        "v neo method mismatch")

        self.assertEqual(expected_spikes, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        read_spikes = numpy.loadtxt(spike_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_spikes, spikes_7),
                        "spikes synakker method mismatch")
        self.assertTrue(numpy.allclose(read_spikes, spikes),
                        "spikes neo method mismatch")

    def test_sampling_rate(self):
        self.runsafe(self.do_sampling_rate)

    def do_all_constraint(self):
        synfire_run = SynfireRunner()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=[runtime],
                           placement_constraint=placement_constraint,
                           record=True, record_7=True, record_v=True,
                           record_v_7=True, record_gsyn_exc=True,
                           record_gsyn_exc_7=True, record_gsyn_inh=False)

        gsyn_exc = synfire_run.get_output_pop_gsyn_exc_numpy()
        v = synfire_run.get_output_pop_voltage_numpy()
        spikes = synfire_run.get_output_pop_spikes_numpy()

        self.assertEqual(n_neurons*runtime, len(gsyn_exc))
        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_gsyn, gsyn_exc, rtol=1e-04),
                        "gsyn neo method mismatch")

        self.assertEqual(n_neurons*runtime, len(v))
        read_v = numpy.loadtxt(v_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_v, v, rtol=1e-03),
                        "v neo method mismatch")

        self.assertEqual(expected_spikes, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        read_spikes = numpy.loadtxt(spike_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_spikes, spikes),
                        "spikes neo method mismatch")

    def test_all_constraint(self):
        self.runsafe(self.do_all_constraint)


if __name__ == '__main__':
    synfire_run = SynfireRunner()
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       delay=delay, run_times=[runtime],
                       placement_constraint=placement_constraint, record=True,
                       record_7=True, record_v=True, record_v_7=True,
                       record_gsyn_exc=True, record_gsyn_exc_7=True,
                       record_gsyn_inh=False)

    gsyn_exc = synfire_run.get_output_pop_gsyn_exc_numpy()
    gsyn_exc_neo = synfire_run.get_output_pop_gsyn_exc_neo()
    v = synfire_run.get_output_pop_voltage_numpy()
    v_neo = synfire_run.get_output_pop_voltage_neo()
    spikes = synfire_run.get_output_pop_spikes_numpy()
    spikes_neo = synfire_run.get_output_pop_spikes_neo()

    numpy.savetxt(spike_file, spikes, delimiter=',')
    numpy.savetxt(v_file, v, delimiter=',')
    numpy.savetxt(gysn_file, gsyn_exc, delimiter=',')

    Figure(SpynnakerPanel(spikes_neo, yticks=True, xticks=True, markersize=4,
                          xlim=(0, runtime)),
           SpynnakerPanel(v_neo, yticks=True, xticks=True),
           SpynnakerPanel(gsyn_exc_neo, yticks=True),
           title="Synfire with delay of {}".format(delay),
           annotations="generated by {}".format(__file__))
    plt.show()

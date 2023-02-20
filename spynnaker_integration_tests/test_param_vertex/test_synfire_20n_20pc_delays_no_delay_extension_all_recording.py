#!/usr/bin/python

# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
delay = 7
runtime = 200
neurons_per_core = None
placement_constraint = (0, 0)
expected_spikes = 22
spike_file = "20_7_spikes.csv"
v_file = "20_7_v.csv"
gysn_file = "20_7_gsyn.csv"


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

        self.assertEqual(n_neurons * runtime, len(gsyn_exc))
        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_gsyn, gsyn_exc_7, rtol=1e-04),
                        "gsyn synakker method mismatch")
        self.assertTrue(numpy.allclose(read_gsyn, gsyn_exc, rtol=1e-04),
                        "gsyn neo method mismatch")

        self.assertEqual(n_neurons * runtime, len(v))
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

        self.assertEqual(n_neurons * runtime, len(gsyn_exc))
        read_gsyn = numpy.loadtxt(gysn_file, delimiter=',')
        self.assertTrue(numpy.allclose(read_gsyn, gsyn_exc, rtol=1e-04),
                        "gsyn neo method mismatch")

        self.assertEqual(n_neurons * runtime, len(v))
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

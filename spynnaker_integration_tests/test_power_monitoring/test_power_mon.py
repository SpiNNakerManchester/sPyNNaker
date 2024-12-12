# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import numpy
import sqlite3
import unittest
import pyNN.spiNNaker as p
from spinn_front_end_common.interface.provenance import ProvenanceReader
from spinn_front_end_common.utilities.report_functions import EnergyReport
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker_integration_tests.scripts import SynfireRunner
from spinnaker_testbase import BaseTestCase

n_neurons = 200  # number of neurons in each population
neurons_per_core = n_neurons / 2
run_times = [10, 20, 30]
# parameters for population 1 first run
input_class = p.SpikeSourcePoisson
start_time = 0
duration = 5000.0
rate = 2.0
synfire_run = SynfireRunner()


class TestPowerMonitoring(BaseTestCase):

    def do_run(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=run_times, input_class=input_class,
                           start_time=start_time, duration=duration, rate=rate,
                           seed=12345)
        spikes = synfire_run.get_output_pop_spikes_numpy()
        self.assertIsNotNone(spikes, "must have some spikes")
        # Check spikes increase in second half by at least a factor of ten
        hist = numpy.histogram(spikes[:, 1], bins=[0, 5000, 10000])
        self.assertIsNotNone(hist, "must have a histogram")
        # Did we build the report file like we asked for in config file?
        self.assertIn(EnergyReport.file_name(1),
                      os.listdir(SpynnakerDataView.get_run_dir_path()))
        self.assertIn(EnergyReport.file_name(2),
                      os.listdir(SpynnakerDataView.get_run_dir_path()))
        self.assertIn(EnergyReport.file_name(3),
                      os.listdir(SpynnakerDataView.get_run_dir_path()))
        # Did we output power provenance data, as requested?
        exec_times = set()
        with ProvenanceReader() as reader:
            for row in reader.execute(
                    "SELECT the_value "
                    "FROM power_provenance "
                    "WHERE description = 'Exec time (seconds)'"):
                exec_times.add(row[0])
        self.assertEqual(exec_times, set([0.01, 0.03, 0.06]))

    def test_power_monitoring(self):
        self.runsafe(self.do_run)

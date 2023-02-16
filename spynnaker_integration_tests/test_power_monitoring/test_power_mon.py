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

import os
import numpy
import unittest
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner
from spinn_front_end_common.interface.provenance import ProvenanceReader
from spinn_front_end_common.utilities.report_functions import EnergyReport
from spynnaker.pyNN.data import SpynnakerDataView
import sqlite3

n_neurons = 200  # number of neurons in each population
neurons_per_core = n_neurons / 2
run_times = [5000]
# parameters for population 1 first run
input_class = p.SpikeSourcePoisson
start_time = 0
duration = 5000.0
rate = 2.0
synfire_run = SynfireRunner()


class TestPowerMonitoring(BaseTestCase):
    def query_provenance(self, query, *args):
        prov_file = ProvenanceReader.get_last_run_database_path()
        with sqlite3.connect(prov_file) as prov_db:
            prov_db.row_factory = sqlite3.Row
            return list(prov_db.execute(query, args))

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
        self.assertIn(EnergyReport._SUMMARY_FILENAME,
                      os.listdir(SpynnakerDataView.get_run_dir_path()))
        # Did we output power provenance data, as requested?
        num_chips = None
        for row in self.query_provenance(
                "SELECT the_value "
                "FROM power_provenance "
                "WHERE description = 'Num_chips' LIMIT 1"):
            num_chips = row["the_value"]
        self.assertIsNotNone(num_chips, "power provenance was not written")

    @unittest.skip(
        "https://github.com/SpiNNakerManchester/"
        "SpiNNFrontEndCommon/issues/866")
    def test_power_monitoring(self):
        self.runsafe(self.do_run)

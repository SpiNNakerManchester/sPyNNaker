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

import os
import numpy
import unittest
import spynnaker8 as p
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner
from spinn_front_end_common.utilities.globals_variables import (
    provenance_file_path, report_default_directory)
from spinn_front_end_common.utilities.report_functions import EnergyReport
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
        prov_file = os.path.join(
            provenance_file_path(), "provenance.sqlite3")
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
                      os.listdir(report_default_directory()))
        # Did we output power provenance data, as requested?
        num_chips = None
        for row in self.query_provenance(
                "SELECT the_value FROM provenance_view "
                "WHERE source_name = 'power_provenance' "
                "AND description_name = 'num_chips' LIMIT 1"):
            num_chips = row["the_value"]
        self.assertIsNotNone(num_chips, "power provenance was not written")

    @unittest.skip(
        "https://github.com/SpiNNakerManchester/SpiNNFrontEndCommon/issues/866")
    def test_power_monitoring(self):
        self.runsafe(self.do_run)

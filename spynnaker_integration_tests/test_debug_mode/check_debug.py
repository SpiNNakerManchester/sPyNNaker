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
from spinn_utilities.config_holder import (
    config_options, get_report_path)

from spinnaker_testbase import BaseTestCase

from spynnaker.pyNN.config_setup import cfg_paths_skipped
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.extra_algorithms.\
    spynnaker_neuron_network_specification_report import (
        _GRAPH_NAME, _GRAPH_FORMAT)
import pyNN.spiNNaker as sim


class CheckDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """
    def assert_reports(self):
        skipped = cfg_paths_skipped()
        for option in config_options("Reports"):
            for option in config_options("Reports"):
                if not option.startswith("path"):
                    continue
                if option in skipped:
                    continue

            path = get_report_path(option)
            print(f"found {option} at {path}")
            if not os.path.exists(path):
                raise AssertionError(
                    f"Unable to find report for {option} {path}")

    def debug(self):
        # pylint: disable=protected-access
        reports = [
            _GRAPH_NAME,
            _GRAPH_NAME + "." +
            _GRAPH_FORMAT,
            ]

        sim.setup(1.0)
        pop = sim.Population(100, sim.IF_curr_exp, {}, label="pop")
        pop.record("v")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        sim.run(0)
        pop.get_data("v")
        run0 = SpynnakerDataView.get_run_dir_path()
        found = os.listdir(run0)
        for report in reports:
            self.assertIn(report, found)
        self.assert_reports()
        self.assertIn("data.sqlite3", found)
        self.assertIn("ds.sqlite3", found)

        sim.run(10)  # second run
        pop.get_data("v")
        self.assertEqual(run0, SpynnakerDataView.get_run_dir_path())
        # No point in checking files they are already there

        sim.reset()  # Soft
        # check get works directly after a reset
        pop.get_data("v")
        sim.run(10)
        found = os.listdir(SpynnakerDataView.get_run_dir_path())
        self.assertIn("data1.sqlite3", found)
        self.assertNotIn("ds1.sqlite3", found)

        sim.reset()  # soft with dsg
        SpynnakerDataView.set_requires_data_generation()
        sim.run(10)
        pop.get_data("v")
        self.assertEqual(run0, SpynnakerDataView.get_run_dir_path())
        found = os.listdir(run0)
        self.assertIn("data2.sqlite3", found)
        self.assertIn("ds2.sqlite3", found)
        # No point in checking files they are already there

        sim.reset()  # hard
        SpynnakerDataView.set_requires_mapping()
        sim.run(10)
        pop.get_data("v")
        self.assertNotEqual(run0, SpynnakerDataView.get_run_dir_path())
        found = os.listdir(SpynnakerDataView.get_run_dir_path())
        for report in reports:
            self.assertIn(report, found)
        self.assert_reports()
        self.assertIn("data3.sqlite3", found)
        self.assertIn("ds3.sqlite3", found)

        sim.end()

    def emptyrun(self):
        """ Chech there is no error on run not done """
        sim.setup(timestep=1.0)
        sim.run(10)
        sim.end()

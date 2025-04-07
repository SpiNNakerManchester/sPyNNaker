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
from spinn_utilities.config_holder import get_config_bool, get_report_path

from spinn_front_end_common.interface.interface_functions \
    import load_using_advanced_monitors
import spinn_front_end_common.utilities.report_functions.reports as \
    reports_names
from spinn_front_end_common.utilities.report_functions.network_specification \
    import _FILENAME as network_specification_file_name
from spinn_front_end_common.utilities.report_functions.drift_report import (
    CLOCK_DRIFT_REPORT)
from spinn_front_end_common.utilities.report_functions.\
    memory_map_on_host_report import _FOLDER_NAME as \
    memory_map_on_host_report
# from spinn_front_end_common.utilities.report_functions.energy_report \
#    import EnergyReport
from spinn_front_end_common.utilities.report_functions.board_chip_report \
    import AREA_CODE_REPORT_NAME
from spinn_front_end_common.utilities.report_functions.\
    fixed_route_from_machine_report import REPORT_NAME as fixed_route_report
from spinn_front_end_common.utility_models import \
     DataSpeedUpPacketGatherMachineVertex
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.extra_algorithms.\
    spynnaker_neuron_network_specification_report import (
        _GRAPH_NAME, _GRAPH_FORMAT)
import pyNN.spiNNaker as sim


class CheckDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """

    def assert_report(self, option):
        path = get_report_path(option)
        if not os.path.exists(path):
            raise AssertionError(f"Unable to find report for {option}")


    def debug(self):
        sim.setup(1.0)
        # pylint: disable=protected-access
        reports = [
            # write_energy_report
            # EnergyReport._DETAILED_FILENAME,
            # EnergyReport._SUMMARY_FILENAME,
            # write_text_specs = False
            "data_spec_text_files",
            # write_memory_map_report
            memory_map_on_host_report,
            # write_network_specification_report
            network_specification_file_name,
            "provenance_data",
            # write_tag_allocation_reports
            reports_names._TAGS_FILENAME,
            # write_drift_report_end or start
            CLOCK_DRIFT_REPORT,
            # write_board_chip_report
            AREA_CODE_REPORT_NAME,
            _GRAPH_NAME,
            _GRAPH_NAME + "." +
            _GRAPH_FORMAT,
            fixed_route_report,
            ]

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
        if (get_config_bool("Machine", "enable_advanced_monitor_support")
                and not get_config_bool("Java", "use_java")):
            # write_data_speed_up_report
            reports.append(
                DataSpeedUpPacketGatherMachineVertex.OUT_REPORT_NAME)
            if load_using_advanced_monitors():
                reports.append(
                    DataSpeedUpPacketGatherMachineVertex.IN_REPORT_NAME)
        for report in reports:
            self.assertIn(report, found)
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
        self.assert_report(reports_names.PATH_COMPRESSED)
        self.assert_report(reports_names.PATH_COMPRESSION_COMPARISON)
        self.assert_report(reports_names.PATH_PARTITIONER_REPORTS)
        self.assert_report(reports_names.PATH_PLACEMENT_REPORTS_VERTEX)
        self.assert_report(reports_names.PATH_PLACEMENT_REPORTS_CORE)
        self.assert_report(reports_names.PATH_ROUTER_REPORTS)
        self.assert_report(reports_names.PATH_ROUTER_REPORTS)
        self.assert_report(reports_names.PATH_SDRAM_USAGE)
        self.assert_report(reports_names.PATH_SUMMARY_REPORT)
        self.assert_report(reports_names.PATH_UNCOMPRESSED)
        self.assertIn("data3.sqlite3", found)
        self.assertIn("ds3.sqlite3", found)

        sim.end()

    def emptyrun(self):
        """ Chech there is no error on run not done """
        sim.setup(timestep=1.0)
        sim.run(10)
        sim.end()

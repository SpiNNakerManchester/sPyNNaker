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
from unittest.case import SkipTest
from requests.exceptions import ConnectionError

from spinn_utilities.config_holder import (
    config_options, get_config_bool, get_report_path)

from spinn_front_end_common.interface.interface_functions \
    import load_using_advanced_monitors
from spinn_front_end_common.utilities.report_functions.drift_report import (
    CLOCK_DRIFT_REPORT)
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
        _GRAPH_NAME)
import pyNN.spiNNaker as sim


class CheckDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """

    def assert_reports(self):
        for option in config_options("Reports"):
            if not option.startswith("path"):
                continue

            if option == "pathenergyreport":
                # enegry reports not run in debug mode
                continue

            if option in ["pathdataspeedupreportsrouters",
                          "pathdataspeedupreportsspeeds"]:
                # not run without advancd monitors
                if not get_config_bool("Machine",
                                       "enable_advanced_monitor_support"):
                    continue
                # not run when using java
                if get_config_bool("Java", "use_java"):
                    continue
                if option == "pathdataspeedupreportsspeeds":
                    # report only created if loading using advanced monitors
                    if not load_using_advanced_monitors():
                        continue

            path = get_report_path(option)
            print(f"found {option} at {path}")
            if not os.path.exists(path):
                raise AssertionError(
                    f"Unable to find report for {option} {path}")

    def debug(self):
        # pylint: disable=protected-access
        reports = [
            # write_energy_report
            # EnergyReport._DETAILED_FILENAME,
            # EnergyReport._SUMMARY_FILENAME,
            # write_text_specs = False
            "data_spec_text_files",
            # repeats reports_names._SDRAM_FILENAME,
            "provenance_data",
            # write_drift_report_end or start
            CLOCK_DRIFT_REPORT,
            _GRAPH_NAME,
            # graphviz exe may not be installed so there will be no image file
            # _GRAPH_NAME + "." + _GRAPH_FORMAT,
            fixed_route_report,
            ]

        sim.setup(1.0)
        pop = sim.Population(100, sim.IF_curr_exp, {}, label="pop")
        pop.record("v")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        try:
            sim.run(0)
        except ConnectionError:
            raise SkipTest("DNS Error Monster!")

        pop.get_data("v")
        run0 = SpynnakerDataView.get_run_dir_path()
        found = os.listdir(run0)
        for report in reports:
            self.assertIn(report, found)
        self.assertIn("data.sqlite3", found)
        self.assertIn("ds.sqlite3", found)
        self.assert_reports()

        sim.run(10)  # second run
        pop.get_data("v")
        self.assertEqual(run0, SpynnakerDataView.get_run_dir_path())

        sim.end()

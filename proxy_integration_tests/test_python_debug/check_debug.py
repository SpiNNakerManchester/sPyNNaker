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
from spinn_utilities.config_holder import get_config_bool

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
        _GRAPH_NAME)
import pyNN.spiNNaker as sim


class CheckDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """
    def debug(self):
        # pylint: disable=protected-access
        reports = [
            # write_energy_report
            # EnergyReport._DETAILED_FILENAME,
            # EnergyReport._SUMMARY_FILENAME,
            # write_text_specs = False
            "data_spec_text_files",
            # write_router_reports
            reports_names._ROUTING_FILENAME,
            # write_partitioner_reports
            reports_names._PARTITIONING_FILENAME,
            # write_application_graph_placer_report
            reports_names._PLACEMENT_VTX_GRAPH_FILENAME,
            reports_names._PLACEMENT_CORE_GRAPH_FILENAME,
            reports_names._SDRAM_FILENAME,
            # repeats reports_names._SDRAM_FILENAME,
            # write_router_info_report
            reports_names._VIRTKEY_FILENAME,
            # write_routing_table_reports
            reports_names._ROUTING_TABLE_DIR,
            reports_names._C_ROUTING_TABLE_DIR,
            reports_names._COMPARED_FILENAME,
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

        sim.end()

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
import spinn_front_end_common.utilities.report_functions.reports as \
    reports_names
from spinn_front_end_common.utilities.report_functions.network_specification \
    import _FILENAME as network_specification_file_name
from spinn_front_end_common.utilities.report_functions.drift_report import (
    CLOCK_DRIFT_REPORT)
from spinn_front_end_common.utilities.report_functions.\
    routing_table_from_machine_report import _FOLDER_NAME as \
    routing_tables_from_machine_report
from spinn_front_end_common.utilities.report_functions.\
    memory_map_on_host_report import _FOLDER_NAME as \
    memory_map_on_host_report
# from spinn_front_end_common.utilities.report_functions.energy_report \
#    import EnergyReport
from spinn_front_end_common.utilities.report_functions.board_chip_report \
    import AREA_CODE_REPORT_NAME
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
            # write_routing_tables_from_machine_report
            routing_tables_from_machine_report,
            # write_memory_map_report
            memory_map_on_host_report,
            # write_network_specification_report
            network_specification_file_name,
            # write_provenance_data
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
            ]

        sim.setup(1.0)
        if (get_config_bool("Machine", "enable_advanced_monitor_support")
                and not get_config_bool("Java", "use_java")):
            # write_data_speed_up_report
            reports.append(
                DataSpeedUpPacketGatherMachineVertex.OUT_REPORT_NAME)
            reports.append(DataSpeedUpPacketGatherMachineVertex.IN_REPORT_NAME)
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
        self.assertIn("data3.sqlite3", found)
        self.assertIn("ds3.sqlite3", found)

        sim.end()

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
            "app_provenance_data",
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
        found = os.listdir(SpynnakerDataView.get_run_dir_path())
        for report in reports:
            self.assertIn(report, found)

        sim.run(10)
        pop.get_data("v")
        # No point in checking files they are already there

        sim.reset()
        pop.get_data("v")
        SpynnakerDataView.set_requires_data_generation()
        sim.run(10)
        pop.get_data("v")
        # No point in checking files they are already there

        sim.reset()
        SpynnakerDataView.set_requires_mapping()
        sim.run(10)
        pop.get_data("v")
        found = os.listdir(SpynnakerDataView.get_run_dir_path())
        for report in reports:
            self.assertIn(report, found)

        sim.end()

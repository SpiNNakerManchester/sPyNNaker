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
import pacman.operations.algorithm_reports.reports as reports_names
from pacman.operations.algorithm_reports.network_specification import \
    NetworkSpecification
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.report_functions.\
    routing_table_from_machine_report import _FOLDER_NAME as \
    routing_tables_from_machine_report
from spinn_front_end_common.utilities.report_functions.energy_report \
    import EnergyReport
from spinn_front_end_common.utilities.report_functions.board_chip_report \
    import BoardChipReport
from spinn_front_end_common.utility_models import \
     DataSpeedUpPacketGatherMachineVertex
from p8_integration_tests.base_test_case import BaseTestCase
import spynnaker8 as sim


class CheckDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """
    def debug(self, run_zero):
        # pylint: disable=protected-access
        reports = [
            # write_energy_report
            EnergyReport._DETAILED_FILENAME,
            EnergyReport._SUMMARY_FILENAME,
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
            # write_machine_graph_placer_report
            reports_names._PLACEMENT_VTX_SIMPLE_FILENAME,
            reports_names._PLACEMENT_CORE_SIMPLE_FILENAME,
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
            # ??? used by MachineExecuteDataSpecification but not called ???
            # write_network_specification_report
            NetworkSpecification._FILENAME,
            # write_provenance_data
            "provenance_data",
            # write_tag_allocation_reports
            reports_names._TAGS_FILENAME,
            # write_algorithm_timings
            # "provenance_data/pacman.xml"  = different test
            # write_board_chip_report
            BoardChipReport.AREA_CODE_REPORT_NAME,
            ]

        sim.setup(1.0)
        configs = globals_variables.get_simulator()._config
        if (configs.getboolean("Machine", "enable_advanced_monitor_support")
                and not configs.getboolean("Java", "use_java")):
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
        if run_zero:
            sim.run(0)
        sim.run(1000)
        pop.get_data("v")
        report_directory = globals_variables.get_simulator().\
            _report_default_directory
        sim.end()

        found = os.listdir(report_directory)
        for report in reports:
            self.assertIn(report, found)

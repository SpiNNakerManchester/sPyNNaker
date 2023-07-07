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
import unittest
import spinn_front_end_common.utilities.report_functions.reports as \
    reports_names
from spinn_front_end_common.utilities.report_functions.network_specification \
    import _FILENAME as network_specification_file_name
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.extra_algorithms.\
    spynnaker_neuron_network_specification_report import (_GRAPH_NAME)
import pyNN.spiNNaker as sim


class TestDebug(BaseTestCase):
    """
    that it does not crash in debug mode. All reports on.
    """

    # NO unittest_setup() as sim.setup is called

    def debug(self):
        reports = [
            # write_energy_report does not happen on a virtual machine
            # "Detailed_energy_report.rpt",
            # "energy_summary_report.rpt",
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
            # write_routing_table_reports not on a virtual boad
            # reports_names._ROUTING_TABLE_DIR,
            # reports_names._C_ROUTING_TABLE_DIR,
            # reports_names._COMPARED_FILENAME,
            # write_routing_compression_checker_report not on a virtual board
            # "routing_compression_checker_report.rpt",
            # write_routing_tables_from_machine_report not on a virtual board
            # routing_tables_from_machine_report,
            # write_memory_map_report
            # ??? used by MachineExecuteDataSpecification but not called ???
            # write_network_specification_report
            network_specification_file_name,
            "data.sqlite3",
            # write_tag_allocation_reports
            reports_names._TAGS_FILENAME,
            # write_algorithm_timings
            # "provenance_data/pacman.xml"  = different test
            # write_board_chip_report not on a virtual board
            # BoardChipReport.AREA_CODE_REPORT_NAME,
            # write_data_speed_up_report not on a virtual board
            # DataSpeedUpPacketGatherMachineVertex.REPORT_NAME
            _GRAPH_NAME,
            # TODO why svg when default is png
            _GRAPH_NAME + ".svg"
            ]
        sim.setup(1.0)
        pop = sim.Population(100, sim.IF_curr_exp, {}, label="pop")
        pop.record("v")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        sim.run(1000)
        pop.get_data("v")
        sim.end()

        found = os.listdir(SpynnakerDataView.get_run_dir_path())
        for report in reports:
            self.assertIn(report, found)
        self.assertIn("ds.sqlite3", found)

    def test_debug(self):
        self.runsafe(self.debug)


if __name__ == '__main__':
    unittest.main()

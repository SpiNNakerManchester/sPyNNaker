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
        sim.setup(1.0)
        pop = sim.Population(100, sim.IF_curr_exp, {}, label="pop")
        pop.record("v")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        sim.run(10)
        sim.end()

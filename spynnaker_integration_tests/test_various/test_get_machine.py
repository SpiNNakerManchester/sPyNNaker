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

import pyNN.spiNNaker as sim
from spinn_utilities.data.reset_status import ResetStatus
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView


class MachineTest(BaseTestCase):

    def do_run(self):
        # pylint: disable=protected-access,no-member
        sim.setup(timestep=1.0, n_boards_required=2)
        pop = sim.Population(3, sim.IF_curr_exp(), label="pop_1")
        # HACK to directly read the underlying models to avoid triggering
        # various autodetection systems. DO NOT COPY AS UNSUPPORTED!
        MachineDataModel = SpynnakerDataView._MachineDataView__data
        UtilsDataModel = SpynnakerDataView._UtilsDataView__data
        self.assertIsNone(MachineDataModel._machine)
        self.assertEqual(
            ResetStatus.SETUP, UtilsDataModel._reset_status, "setup")
        self.assertTrue(SpynnakerDataView.get_requires_mapping())

        sim.run(1)
        machine1 = MachineDataModel._machine
        self.assertEqual(
            ResetStatus.HAS_RUN, UtilsDataModel._reset_status, "run 1")
        # a call to initialize should not force a hard reset
        pop.initialize(v=-64)
        sim.run(2)

        # Same machine after second run
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine1), "run 2")

        sim.reset()  # 1 soft as no get_machine detected
        self.assertEqual(
            ResetStatus.SOFT_RESET, UtilsDataModel._reset_status, "reset 1")
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine1), "reset 1")
        self.assertFalse(SpynnakerDataView.get_requires_mapping(), "reset 1")

        sim.run(3)
        self.assertFalse(MachineDataModel._user_accessed_machine, "run 3")
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine1), "run 3")
        self.assertTrue(MachineDataModel._user_accessed_machine, "run 3 get")

        sim.reset()  # 2 hard due to get_machine
        self.assertEqual(ResetStatus.HARD_RESET, UtilsDataModel._reset_status)
        self.assertFalse(MachineDataModel._user_accessed_machine)
        self.assertTrue(SpynnakerDataView.get_requires_mapping(), "reset 2")
        self.assertIsNone(MachineDataModel._machine)

        sim.run(4)
        self.assertEqual(ResetStatus.HAS_RUN, UtilsDataModel._reset_status)
        self.assertFalse(MachineDataModel._user_accessed_machine)
        machine2 = MachineDataModel._machine
        self.assertNotEqual(id(machine2), id(machine1), "run 4")

        sim.reset()  # 3 soft reset as no new detectable get machine
        self.assertEqual(ResetStatus.SOFT_RESET, UtilsDataModel._reset_status)
        self.assertFalse(MachineDataModel._user_accessed_machine)
        machine = MachineDataModel._machine
        self.assertFalse(SpynnakerDataView.get_requires_mapping(), "reset 3")

        self.assertEqual(id(machine), id(machine2), "reset 3")
        sim.run(5)
        self.assertFalse(MachineDataModel._user_accessed_machine)
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine2), "run 5")

        sim.reset()  # 4 Will become hard due to new pop
        self.assertEqual(ResetStatus.SOFT_RESET, UtilsDataModel._reset_status)
        self.assertFalse(MachineDataModel._user_accessed_machine)
        # Hard reset not yet done
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine2), "reset 4")
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        self.assertFalse(MachineDataModel._user_accessed_machine)
        self.assertTrue(SpynnakerDataView.get_requires_mapping(), "reset 4")

        sim.run(6)
        self.assertFalse(SpynnakerDataView.get_requires_mapping(), "run 6")
        machine3 = MachineDataModel._machine
        self.assertNotEqual(id(machine3), id(machine2), "run 6")

        sim.reset()  # 5 soft reset as no new detectable get machine
        self.assertEqual(ResetStatus.SOFT_RESET, UtilsDataModel._reset_status)
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine3), "reset 5")
        self.assertFalse(MachineDataModel._user_accessed_machine, "reset 5")
        self.assertFalse(SpynnakerDataView.get_requires_mapping(), "reset 5")

        sim.run(7)
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine3), "run 7")
        self.assertFalse(MachineDataModel._user_accessed_machine)

        sim.reset()  # 6 Will become hard when get_machine called
        self.assertEqual(ResetStatus.SOFT_RESET, UtilsDataModel._reset_status)
        self.assertFalse(MachineDataModel._user_accessed_machine)
        machine = MachineDataModel._machine
        self.assertEqual(id(machine), id(machine3), "reset 6")
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "reset 6")

        # This should create a new machine
        machine = sim.get_machine()
        machine4 = MachineDataModel._machine
        self.assertNotEqual(id(machine4), id(machine3), "reset 6")

        sim.run(8)
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine4), "run 8")

        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

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

import pyNN.spiNNaker as sim
from spinn_utilities.data.reset_status import ResetStatus
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView


class MachineTest(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0, n_boards_required=2)
        pop = sim.Population(3, sim.IF_curr_exp(), label="pop_1")
        # HACK to avoid detecting user accessed machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertIsNone(SpynnakerDataView._MachineDataView__data._machine)
        self.assertEqual(
            ResetStatus.SETUP,
            SpynnakerDataView._UtilsDataView__data._reset_status, "setup")
        self.assertTrue(
            SpynnakerDataView.get_requires_mapping())

        sim.run(1)
        # HACK to avoid detecting user accessed machine
        machine1 = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(
            ResetStatus.HAS_RUN,
            SpynnakerDataView._UtilsDataView__data._reset_status, "run 1")
        # a call to initialize should not force a hard reset
        pop.initialize(v=-64)
        sim.run(2)

        # Same machine after second run
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "run 2")

        sim.reset()  # 1 soft as no get_machine detected
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status, "reset 1")
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 1")
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "reset 1")

        sim.run(3)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "run 3")
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine1), "run 3")
        self.assertTrue(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "run 3 get")

        sim.reset()  # 2 hard due to get_machine
        self.assertEqual(
            ResetStatus.HARD_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "reset 2")
        # HACK to avoid detecting user accessed machine
        self.assertIsNone(SpynnakerDataView._MachineDataView__data._machine)

        sim.run(4)
        self.assertEqual(
            ResetStatus.HAS_RUN,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        machine2 = SpynnakerDataView._MachineDataView__data._machine
        self.assertNotEqual(id(machine2), id(machine1), "run 4")

        sim.reset()  # 3 soft reset as no new detectable get machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "reset 3")

        self.assertEqual(id(machine), id(machine2), "reset 3")
        sim.run(5)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine2), "run 5")

        sim.reset()  # 4 Will become hard due to new pop
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # Hard reset not yet done
        # HACK to avoid creating a new machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine2), "reset 4")
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        self.assertTrue(
            SpynnakerDataView.get_requires_mapping(), "reset 4")

        sim.run(6)
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "run 6")
        machine3 = SpynnakerDataView._MachineDataView__data._machine
        self.assertNotEqual(id(machine3), id(machine2), "run 6")

        sim.reset()  # 5 soft reset as no new detectable get machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine3), "reset 5")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "reset 5")
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "reset 5")

        sim.run(7)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine3), "run 7")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)

        sim.reset()  # 6 Will become hard when get_machine called
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid creating a new machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine3), "reset 6")
        self.assertFalse(
            SpynnakerDataView.get_requires_mapping(), "reset 6")

        # This should create a new machine
        machine = sim.get_machine()
        machine4 = SpynnakerDataView._MachineDataView__data._machine
        self.assertNotEqual(id(machine4), id(machine3), "reset 6")

        sim.run(8)
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine4), "run 8")

        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

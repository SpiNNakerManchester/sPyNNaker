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

from unittest import SkipTest
import pyNN.spiNNaker as sim
from spinn_utilities.data.reset_status import ResetStatus
from spinn_utilities.exceptions import DataNotYetAvialable
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView


class MachineTest(BaseTestCase):

    def do_flexi(self):
        """
        The behaviour of machine is by design

        The behaviour of transceiver and ip address is by implementation

        """
        sim.setup(timestep=1.0)
        pop = sim.Population(3, sim.IF_curr_exp(), label="pop_1")
        if SpynnakerDataView.has_fixed_machine():
            raise SkipTest("This test only works with spalloc")
        # HACK to avoid detecting user accessed machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertIsNone(SpynnakerDataView._MachineDataView__data._machine)
        self.assertFalse(SpynnakerDataView.has_transceiver())
        self.assertFalse(SpynnakerDataView.has_ipaddress())
        self.assertEqual(
            ResetStatus.SETUP,
            SpynnakerDataView._UtilsDataView__data._reset_status, "setup")
        self.assertTrue(
            SpynnakerDataView.get_vertices_or_edges_added(), "setup")

        sim.run(1)
        # HACK to avoid detecting user accessed machine
        machine1 = SpynnakerDataView._MachineDataView__data._machine
        trans1 = SpynnakerDataView.get_transceiver()
        ip1 = SpynnakerDataView.get_ipaddress()
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
        trans1 = SpynnakerDataView.get_transceiver()
        ip1 = SpynnakerDataView.get_ipaddress()

        sim.reset()  # 1 soft as no get_machine detected
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status, "reset 1")
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine1), "reset 1")
        self.assertEqual(id(trans), id(trans1), "reset 1")
        self.assertEqual(id(ip), id(ip1), "reset 1")
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 1")

        sim.run(3)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "run 3")
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine1), "run 3")
        self.assertEqual(id(trans), id(trans1), "run 3")
        self.assertEqual(id(ip), id(ip1), "run 3")
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
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 2")
        # HACK to avoid detecting user accessed machine
        self.assertIsNone(SpynnakerDataView._MachineDataView__data._machine)
        self.assertFalse(SpynnakerDataView.has_transceiver())
        self.assertFalse(SpynnakerDataView.has_ipaddress())

        sim.run(4)
        self.assertEqual(
            ResetStatus.HAS_RUN,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        machine2 = SpynnakerDataView._MachineDataView__data._machine
        trans2 = SpynnakerDataView.get_transceiver()
        ip2 = SpynnakerDataView.get_ipaddress()
        self.assertNotEqual(id(machine2), id(machine1), "run 4")
        self.assertNotEqual(id(trans2), id(trans1), "run 4")
        self.assertNotEqual(id(ip), id(ip2), "run 4")

        sim.reset()  # 3 soft reset as no new detectable get machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 3")

        self.assertEqual(id(machine), id(machine2), "reset 3")
        self.assertEqual(id(trans), id(trans2), "reset 3")
        self.assertEqual(id(ip), id(ip2), "reset 3")
        sim.run(5)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine2), "run 5")
        self.assertEqual(id(trans), id(trans2), "run 5")
        self.assertEqual(id(ip), id(ip2), "run 5")

        sim.reset()  # 4 Will become hard due to new pop
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # Hard reset not yet done
        # HACK to avoid creating a new machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine2), "reset 4")
        self.assertEqual(id(trans), id(trans2), "reset 4")
        self.assertEqual(id(ip), id(ip2), "reset 3")
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        self.assertTrue(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 4")

        sim.run(6)
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "run 6")
        machine3 = SpynnakerDataView._MachineDataView__data._machine
        trans3 = SpynnakerDataView.get_transceiver()
        ip3 = SpynnakerDataView.get_ipaddress()
        self.assertNotEqual(id(machine3), id(machine2), "run 6")
        self.assertNotEqual(id(trans3), id(trans2), "run 6")
        self.assertNotEqual(id(ip3), id(ip2), "run 6")

        sim.reset()  # 5 soft reset as no new detectable get machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine3), "reset 5")
        self.assertEqual(id(trans), id(trans3), "reset 5")
        self.assertEqual(id(ip), id(ip3), "reset 5")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "reset 5")
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 5")

        sim.run(7)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine3), "run 7")
        self.assertEqual(id(trans), id(trans3), "run 7")
        self.assertEqual(id(ip), id(ip3), "run 7")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)

        sim.reset()  # 6 Will not become hard as get Machine errors
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid creating a new machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine3), "reset 6")
        self.assertEqual(id(trans), id(trans3), "reset 6")
        self.assertEqual(id(ip), id(ip3), "reset 6")
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 6")

        with self.assertRaises(DataNotYetAvialable):
                sim.get_machine()

        sim.run(8)
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        trans = SpynnakerDataView.get_transceiver()
        ip = SpynnakerDataView.get_ipaddress()
        self.assertEqual(id(machine), id(machine3), "run 8")
        self.assertEqual(id(trans), id(trans3), "run 8")
        self.assertEqual(id(ip), id(ip3), "run 8")

        sim.end()

    def do_fixed(self):
        sim.setup(timestep=1.0, n_boards_required=2)
        pop = sim.Population(3, sim.IF_curr_exp(), label="pop_1")
        # HACK to avoid detecting user accessed machine
        # DO NOT COPY AS UNSUPPORTED
        machine1 = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(
            ResetStatus.SETUP,
            SpynnakerDataView._UtilsDataView__data._reset_status, "setup")
        self.assertTrue(
            SpynnakerDataView.get_vertices_or_edges_added(), "setup")

        sim.run(1)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        # Same machine after run
        self.assertEqual(id(machine), id(machine1), "run 2")
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
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 1")

        sim.run(3)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "run 3")
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine1), "run 3")
        # never set of fixed machine
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "run 3 get")

        sim.reset()  # 2 soft due to fixed get_machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 2")
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 2")

        sim.run(4)
        self.assertEqual(
            ResetStatus.HAS_RUN,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "run 4")

        sim.reset()  # 3 soft reset as no new detectable get machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 3")

        self.assertEqual(id(machine), id(machine1), "reset 3")
        sim.run(5)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "run 5")

        sim.reset()  # 4 Will become hard due to new pop
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # Hard reset not yet done
        # HACK to avoid creating a new machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 4")
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        self.assertTrue(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 4")

        sim.run(6)
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "run 6")
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "run 6")

        sim.reset()  # 5 soft reset as no new detectable get machine
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 5")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine,
            "reset 5")
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 5")

        sim.run(7)
        # HACK to avoid detecting user accessed machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "run 7")
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)

        sim.reset()  # 6 Will not become hard when get_machine called
        self.assertEqual(
            ResetStatus.SOFT_RESET,
            SpynnakerDataView._UtilsDataView__data._reset_status)
        self.assertFalse(
            SpynnakerDataView._MachineDataView__data._user_accessed_machine)
        # HACK to avoid creating a new machine
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 6")
        self.assertFalse(
            SpynnakerDataView.get_vertices_or_edges_added(), "reset 6")

        # This should not create a new machine
        machine = sim.get_machine()
        self.assertEqual(id(machine), id(machine1), "reset 6a")
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 6b")

        sim.run(8)
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine1), "run 8")

        sim.end()

    def test_run_flexi(self):
        self.runsafe(self.do_flexi)

    def test_run_fixed(self):
        self.runsafe(self.do_fixed)

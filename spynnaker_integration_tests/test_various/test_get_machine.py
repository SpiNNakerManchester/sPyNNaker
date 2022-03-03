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

import spynnaker8 as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView


class MachineTest(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0, n_boards_required=2)
        sim.Population(3, sim.IF_curr_exp(), label="pop_1")
        # HACK to avoid detecting we do not yet have a machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertIsNone(SpynnakerDataView._MachineDataView__data._machine)

        sim.run(1)
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        id1 = id(SpynnakerDataView._MachineDataView__data._machine)
        sim.run(2)

        # Same machine after second run
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertEqual(
            id1, id(SpynnakerDataView._MachineDataView__data._machine), "run2")

        sim.reset()  # soft as no get_machine detected
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertEqual(
            id1, id(SpynnakerDataView._MachineDataView__data._machine), "run2")
        sim.run(3)
        self.assertEqual(id1, id(sim.get_machine()), "run3")

        sim.reset()  # hard due to get_machine
        id2 = id(sim.get_machine())
        self.assertNotEqual(id1, id2, "hard reset")
        sim.run(4)
        self.assertEqual(id2, id(sim.get_machine()), "run4")

        sim.reset()  # hard due to get_machine
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        id3 = id(SpynnakerDataView._MachineDataView__data._machine)
        sim.run(5)
        self.assertEqual(
            id3, id(SpynnakerDataView._MachineDataView__data._machine), "run5")

        sim.reset()  # Will become hard due to new pop
        # Hard reset not yet done
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertEqual(
            id3, id(SpynnakerDataView._MachineDataView__data._machine),
            "not hard yet")
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        sim.run(6)
        id4 = id(SpynnakerDataView._MachineDataView__data._machine)
        self.assertNotEqual(id3, id4, "run6")
        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

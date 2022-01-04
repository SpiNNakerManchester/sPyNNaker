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


class MachineTest(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0, n_boards_required=2)
        sim.Population(3, sim.IF_curr_exp(), label="pop_1")
        machine1 = sim.get_machine()
        id1 = id(machine1)
        sim.run(1)
        machine2 = sim.get_machine()
        id2 = id(machine2)
        self.assertEqual(id1, id2)
        sim.run(2)

        machine3 = sim.get_machine()
        id3 = id(machine3)
        self.assertEqual(id1, id3)

        sim.reset()  # soft
        sim.run(3)
        machine4 = sim.get_machine()
        id4 = id(machine4)
        self.assertEqual(id1, id4)

        sim.reset()  # hard due to get_machine
        machine5 = sim.get_machine()
        id5 = id(machine5)
        self.assertNotEqual(id4, id5)
        self.assertNotEqual(id1, id5)
        sim.run(3)

        machine6 = sim.get_machine()
        id6 = id(machine6)
        self.assertEqual(id5, id6)

        sim.reset()  # Hard due to new pop
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        sim.run(3)
        machine7 = sim.get_machine()
        id7 = id(machine7)
        self.assertNotEqual(id1, id7)
        self.assertNotEqual(id5, id7)

        sim.reset()  # soft
        sim.run(3)
        machine8 = sim.get_machine()
        id8 = id(machine8)
        self.assertEqual(id7, id8)

        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

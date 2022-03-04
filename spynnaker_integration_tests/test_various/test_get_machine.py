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
        machine1 = SpynnakerDataView._MachineDataView__data._machine
        sim.run(2)

        # Same machine after second run
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "run 2")

        sim.reset()  # soft as no get_machine detected
        # HACK to avoid creating a new machine
        # DO NOT COPY AS UNSUPPORTED
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine1), "reset 1")
        sim.run(3)
        # Normal detected get machine
        machine = SpynnakerDataView.get_machine()
        self.assertEqual(id(machine), id(machine1), "run 3")

        sim.reset()  # hard due to get_machine
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        self.assertIsNone(SpynnakerDataView._MachineDataView__data._machine)
        sim.run(4)
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        machine2 = SpynnakerDataView._MachineDataView__data._machine
        print(f"cyab 1:{id(machine1)} 2:{id(machine2)}")
        self.assertNotEqual(id(machine2), id(machine1), "run 4")

        sim.reset()  # soft reset as no new detectable get machine
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine2))
        sim.run(5)
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine2), "run 5")

        sim.reset()  # Will become hard due to new pop
        # Hard reset not yet done
        # HACK to avoid detecting we have a machine
        # DO NOT COPY AS UNSUPPORTED
        machine = SpynnakerDataView._MachineDataView__data._machine
        self.assertEqual(id(machine), id(machine2), "reset 3")
        sim.Population(3, sim.IF_curr_exp(), label="pop_2")
        sim.run(6)
        machine3 = SpynnakerDataView._MachineDataView__data._machine
        self.assertNotEqual(id(machine3), id(machine2), "run 6")

    def test_run(self):
        self.runsafe(self.do_run)

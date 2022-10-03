# Copyright (c) 2017-2022 The University of Manchester
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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestInitialize(BaseTestCase):

    def set_initialize_between_runs(self):
        runtime1 = 5
        runtime2 = 5

        p.setup(timestep=1.0)

        pop = p.Population(3, p.IF_curr_exp())
        pop.record(['v'])

        # At start, initial values are defaults
        self.assertEquals([-65, -65, -65], pop.initial_values["v"])

        # Set to new value and check
        pop.initialize(v=-64)
        self.assertEquals([-64, -64, -64], pop.initial_values["v"])

        p.run(runtime1)
        # After run, the initial values are the same as they were set to
        self.assertEquals([-64, -64, -64], pop.initial_values["v"])

        # Try now setting the state
        pop.set_state(v=-62)
        self.assertEquals([-62, -62, -62], pop.current_values["v"])
        p.run(runtime2)
        # Initial values should not have changed
        self.assertEquals([-64, -64, -64], pop.initial_values["v"])

        id_mixin = pop[1]
        id_mixin.initialize(v=-60)
        # v on not changed is still the initial value
        self.assertEquals(-64, pop.initial_values["v"][0])
        self.assertEquals(-60, pop.initial_values["v"][1])
        self.assertEquals(-64, pop.initial_values["v"][2])
        # Do an additional run to get values at end below
        p.run(1)

        p.reset()
        self.assertEquals([-64, -60, -64], pop.initial_values["v"])
        self.assertEquals([-64, -60, -64], pop.current_values["v"])
        pop.initialize(isyn_exc=-0.1)
        self.assertEquals([-64, -60, -64], pop.initial_values["v"])
        self.assertEquals([-64, -60, -64], pop.current_values["v"])
        p.run(runtime1)
        self.assertEquals([-64, -60, -64], pop.initial_values["v"])
        view = pop[0:2]
        view.set_state(v=-63)
        self.assertEquals(-63, pop.current_values["v"][0])
        self.assertEquals(-63, pop.current_values["v"][1])
        self.assertEquals(-64, pop.initial_values["v"][2])
        p.run(runtime2)

        neo = pop.get_data('v')
        p.end()

        v0 = neo.segments[0].filter(name='v')[0]
        self.assertListEqual(list(v0[0]), [-64, -64, -64])
        self.assertListEqual(list(v0[runtime1]), [-62.0, -62, -62])

        v1 = neo.segments[1].filter(name='v')[0]
        self.assertListEqual(list(v1[0]), [-64.0, -60, -64])
        assert v1[runtime1][0] == -63.0
        assert v1[runtime1][1] == -63.0

    def test_set_initial_value_between_runs(self):
        self.runsafe(self.set_initialize_between_runs)

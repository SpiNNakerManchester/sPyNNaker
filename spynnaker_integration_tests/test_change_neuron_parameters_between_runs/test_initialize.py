# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        self.assertEqual([-65, -65, -65], pop.initial_values["v"])

        # Set to new value and check
        pop.initialize(v=-64)
        self.assertEqual([-64, -64, -64], pop.initial_values["v"])

        p.run(runtime1)
        # After run, the initial values are the same as they were set to
        self.assertEqual([-64, -64, -64], pop.initial_values["v"])

        # Try now setting the state
        pop.set_state(v=-62)
        self.assertEqual([-62, -62, -62], pop.current_values["v"])
        p.run(runtime2)
        # Initial values should not have changed
        self.assertEqual([-64, -64, -64], pop.initial_values["v"])

        id_mixin = pop[1]
        id_mixin.initialize(v=-60)
        # v on not changed is still the initial value
        self.assertEqual(-64, pop.initial_values["v"][0])
        self.assertEqual(-60, pop.initial_values["v"][1])
        self.assertEqual(-64, pop.initial_values["v"][2])
        # Do an additional run to get values at end below
        p.run(1)

        p.reset()
        self.assertEqual([-64, -60, -64], pop.initial_values["v"])
        self.assertEqual([-64, -60, -64], pop.current_values["v"])
        pop.initialize(isyn_exc=-0.1)
        self.assertEqual([-64, -60, -64], pop.initial_values["v"])
        self.assertEqual([-64, -60, -64], pop.current_values["v"])
        p.run(runtime1)
        self.assertEqual([-64, -60, -64], pop.initial_values["v"])
        view = pop[0:2]
        view.set_state(v=-63)
        self.assertEqual(-63, pop.current_values["v"][0])
        self.assertEqual(-63, pop.current_values["v"][1])
        self.assertEqual(-64, pop.initial_values["v"][2])
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

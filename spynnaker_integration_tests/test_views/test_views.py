# Copyright (c) 2017-2023 The University of Manchester
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

import numpy
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestViews(BaseTestCase):

    def set_with_views(self):
        sim.setup(1.0)
        pop = sim.Population(5, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop[2:4].set(i_offset=2.0)
        pop[1, 3].initialize(v=-60)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        v1 = pop.spinnaker_get_data('v')
        sim.end()
        expected = [
            -65., -64.02465820, -63.09686279, -62.21432495, -61.37481689,
            -60., -59.26849365, -58.57263184, -57.91070557, -57.28106689,
            -65., -63.04931641, -61.19375610, -59.42868042, -57.74966431,
            -60., -58.29315186, -56.66952515, -55.12509155, -53.65597534,
            -65., -64.02465820, -63.09686279, -62.21432495, -61.37481689]
        assert numpy.allclose(v1[:, 2], expected)

    def test_initial_value_random(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(5, sim.IF_curr_exp(), label="pop_1")
        self.assertEqual([-65, -65, -65, -65, -65], pop.initial_values["v"])
        view = sim.PopulationView(pop, [1, 3], label="Odds")
        rand_distr = sim.RandomDistribution(
            "uniform", parameters_pos=[-65.0, -55.0],
            rng=sim.NumpyRNG(seed=85524))
        view.initialize(v=rand_distr)
        sim.run(0)
        for val in view.initial_values["v"]:
            self.assertGreaterEqual(val, -65.0)
            self.assertLessEqual(val, -55.0)
        sim.end()

    def test_set_with_views(self):
        self.runsafe(self.set_with_views)

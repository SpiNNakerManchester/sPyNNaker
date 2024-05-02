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
from spinnaker_testbase import BaseTestCase


class TestAllToAllConnector(BaseTestCase):

    def check_weights(self, projection, sources, destinations):
        weights = projection.get(["weight"], "list")
        s_d_set = set((s, d) for s, d, _ in weights)
        self.assertEqual(len(weights), sources * destinations)
        self.assertEqual(len(s_d_set), sources * destinations)

    def check_other_connect(self, sources, destinations):
        sim.setup(1.0)
        pop1 = sim.Population(sources, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(destinations, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.AllToAllConnector(), synapse_type=synapse_type)
        sim.run(1)
        self.check_weights(projection, sources, destinations)
        sim.end()

    def same(self):
        self.check_other_connect(5, 5)

    def test_same(self):
        self.runsafe(self.same)

    def less_sources(self):
        self.check_other_connect(5, 10)

    def test_less_sources(self):
        self.runsafe(self.less_sources)

    def less_destinations(self):
        self.check_other_connect(10, 5)

    def test_less_destinations(self):
        self.runsafe(self.less_destinations)

    def many(self):
        self.check_other_connect(500, 500)

    def test_many(self):
        self.runsafe(self.many)

    def get_before_run(self):
        sim.setup(1.0)
        pop1 = sim.Population(3, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(3, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.AllToAllConnector(),
            synapse_type=synapse_type)
        weights = projection.get(["weight"], "list")
        sim.run(0)
        length = len(weights)
        self.assertEqual(9, length)
        sim.end()

    def test_get_before_run(self):
        self.runsafe(self.get_before_run)

    def using_static_synapse_singles(self):
        sim.setup(timestep=1.0)
        input = sim.Population(2, sim.SpikeSourceArray([0]), label="input")
        pop = sim.Population(2, sim.IF_curr_exp(), label="pop")
        conn = sim.Projection(input, pop, sim.AllToAllConnector(),
                              sim.StaticSynapse(weight=0.7, delay=3))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        target = [(0, 0, 0.7, 3), (0, 1, 3, 33), (1, 0, 0.4, 12),
                  (1, 1, 0.5, 21)]
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(weights[i][j], target[i][j], places=3)

    def test_using_static_synapse_singles(self):
        self.runsafe(self.using_static_synapse_singles)

    def using_population_views(self):
        sim.setup(timestep=1.0)
        input = sim.Population(4, sim.SpikeSourceArray([0]), label="input")
        pop = sim.Population(4, sim.IF_curr_exp(), label="pop")
        conn = sim.Projection(input[1:3], pop[2:4], sim.AllToAllConnector(),
                              sim.StaticSynapse(weight=0.5, delay=2))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        target = [[1, 2, 0.5, 2.], [1, 3, 0.5, 2.], [2, 2, 0.5, 2.],
                  [2, 3, 0.5, 2.]]
        self.assertCountEqual(weights, target)

    def test_using_population_views(self):
        self.runsafe(self.using_population_views)

    def do_all_to_all_nd_test(
            self, neurons_per_core_pre, pre_size, pre_shape,
            neurons_per_core_post, post_size, post_shape):
        sim.setup(1.0)
        pre = sim.Population(
            pre_size, sim.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = sim.Population(
            post_size, sim.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)
        proj = sim.Projection(
            pre, post, sim.AllToAllConnector(),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = set((int(i), int(j)) for i, j in proj.get([], "list"))
        sim.end()

        for i in range(pre_size):
            for j in range(post_size):
                assert (i, j) in conns

    def test_3d_to_1d(self):
        self.do_all_to_all_nd_test(
            (3, 2, 4), 9 * 4 * 8, sim.Grid3D(9 / 4, 9 / 8),
            11, 100, None)

    def test_2d(self):
        self.do_all_to_all_nd_test((3, 5), 9 * 10, sim.Grid2D(9 / 10),
                                   (2, 4), 6 * 8, sim.Grid2D(6 / 8))

    def test_1d_to_2d(self):
        self.do_all_to_all_nd_test(6, 90, None,
                                   (3, 4), 9 * 8, sim.Grid2D(9 / 8))

    def do_all_to_all_nd_self_test(
            self, neurons_per_core, size, shape, self_connect):
        sim.setup(1.0)
        pop = sim.Population(
            size, sim.IF_curr_exp(), structure=shape)
        pop.set_max_atoms_per_core(neurons_per_core)
        proj = sim.Projection(
            pop, pop, sim.AllToAllConnector(
                allow_self_connections=self_connect),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = set((int(i), int(j)) for i, j in proj.get([], "list"))
        sim.end()

        for i in range(size):
            for j in range(size):
                if not self_connect and i == j:
                    assert (i, j) not in conns
                else:
                    assert (i, j) in conns

    def test_3d_no_self_connect(self):
        self.do_all_to_all_nd_self_test(
            (2, 3, 4), 6 * 6 * 8, sim.Grid3D(6 / 6, 6 / 8), self_connect=False)

    def test_2d_self_connect(self):
        self.do_all_to_all_nd_self_test(
            (3, 5), 6 * 15, sim.Grid2D(6 / 15), self_connect=True)

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
import numpy
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestFromListConnectorMixed(BaseTestCase):

    def do_run(self):
        sim.setup(1.0)
        pre = sim.Population(2, sim.IF_curr_exp())
        post = sim.Population(2, sim.IF_curr_exp())
        nrng = sim.NumpyRNG(seed=1)

        # Test case where weights are in list and delays given by random dist
        list1 = [(0, 0, 2.1), (0, 1, 2.6), (1, 1, 3.2)]
        proj1 = sim.Projection(
            pre, post, sim.FromListConnector(list1, column_names=["weight"]),
            sim.StaticSynapse(
                weight=0.5,
                delay=sim.RandomDistribution('uniform', [1, 10], rng=nrng)))

        # Test case where delays are in list and weights given by random dist
        list2 = [(0, 0, 2), (0, 1, 6), (1, 1, 3)]
        proj2 = sim.Projection(
            pre, post, sim.FromListConnector(list2, column_names=["delay"]),
            sim.StaticSynapse(
                weight=sim.RandomDistribution('uniform', [1.5, 3.5], rng=nrng),
                delay=4))

        sim.run(1)
        conns1 = proj1.get(["weight", "delay"], "list")
        conns2 = proj2.get(["weight", "delay"], "list")
        sim.end()

        target1 = [(0, 0, 2.1, 8), (0, 1, 2.6, 6), (1, 1, 3.2, 4)]
        target2 = [(0, 0, 1.7864, 2), (0, 1, 2.0823, 6), (1, 1, 2.4995, 3)]

        # assertAlmostEqual doesn't work on lists, so loop required
        for i in range(3):
            for j in range(2):
                self.assertAlmostEqual(
                    conns1[i][j+2], target1[i][j+2], places=3)
                self.assertAlmostEqual(
                    conns2[i][j+2], target2[i][j+2], places=3)

    def test_from_list_connector_mixed(self):
        self.runsafe(self.do_run)

    def do_list_nd_run(
            self, neurons_per_core_pre, pre_size, pre_shape,
            neurons_per_core_post, post_size, post_shape):
        random_conns = numpy.unique(numpy.random.randint(
            0, (pre_size, post_size), (100, 2)), axis=0)
        sim.setup(1.0)
        pre = sim.Population(
            pre_size, sim.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = sim.Population(
            post_size, sim.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)
        proj = sim.Projection(
            pre, post, sim.FromListConnector(random_conns),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        sim.end()

        c1 = numpy.sort(conns)
        c2 = numpy.sort(random_conns)

        assert numpy.array_equal(c1, c2)

    def test_list_3d_to_1d(self):
        self.do_list_nd_run(
            (3, 4, 2), 3 * 8 * 8, sim.Grid3D(3 / 8, 3 / 8),
            11, 30, None)

    def test_list_2d(self):
        self.do_list_nd_run(
            (5, 3), 10 * 15, sim.Grid2D(10 / 15),
            (1, 6), 6 * 24, sim.Grid2D(6 / 24))

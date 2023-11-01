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
import numpy
from spinnaker_testbase import BaseTestCase

CURR_WEIGHT = 5.0
COND_WEIGHT = 0.1
DELAY = 1.0


class TestOneToOneConnector(BaseTestCase):

    def do_one_to_one_test(self, neurons_per_core, pre_size, post_size):
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, neurons_per_core)
        pre = sim.Population(pre_size, sim.SpikeSourceArray(
            [[i % 100] for i in range(pre_size)]))
        post = sim.Population(post_size, sim.IF_curr_exp())
        post.record("spikes")
        proj = sim.Projection(
            pre, post, sim.OneToOneConnector(),
            sim.StaticSynapse(weight=CURR_WEIGHT, delay=DELAY))
        sim.run(110)
        conns = proj.get(["weight", "delay"], "list")
        spikes = post.get_data("spikes").segments[0].spiketrains
        sim.end()
        for pre, post, w, d in conns:
            assert pre == post
            assert w == CURR_WEIGHT
            assert d == DELAY
        for i in range(min(pre_size, post_size)):
            assert len(spikes[i]) == 1
            assert spikes[i][0] > (i % 100)

    def do_one_to_one_cond_test(self, neurons_per_core, pre_size, post_size):
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_cond_exp, neurons_per_core)
        pre = sim.Population(pre_size, sim.SpikeSourceArray(
            [[i % 100] for i in range(pre_size)]))
        post = sim.Population(post_size, sim.IF_cond_exp())
        post.record("spikes")
        proj = sim.Projection(
            pre, post, sim.OneToOneConnector(),
            sim.StaticSynapse(weight=COND_WEIGHT, delay=DELAY))
        sim.run(110)
        conns = proj.get(["weight", "delay"], "list")
        spikes = post.get_data("spikes").segments[0].spiketrains
        sim.end()
        for pre, post, w, d in conns:
            assert pre == post
            assert numpy.allclose(w, COND_WEIGHT, rtol=0.0001)
            assert d == DELAY
        for i in range(min(pre_size, post_size)):
            assert len(spikes[i]) == 1
            assert spikes[i][0] > (i % 100)

    def do_one_to_one_nd_test(
            self, neurons_per_core_pre, pre_size, pre_shape,
            neurons_per_core_post, post_size, post_shape):
        sim.setup(1.0)
        pre = sim.Population(pre_size, sim.SpikeSourceArray(
            [[i % 100] for i in range(pre_size)]), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = sim.Population(
            post_size, sim.IF_curr_exp(), structure=post_shape)
        post.record("spikes")
        post.set_max_atoms_per_core(neurons_per_core_post)
        proj = sim.Projection(
            pre, post, sim.OneToOneConnector(),
            sim.StaticSynapse(weight=CURR_WEIGHT, delay=DELAY))
        sim.run(110)
        conns = proj.get(["weight", "delay"], "list")
        spikes = post.get_data("spikes").segments[0].spiketrains
        sim.end()
        for pre, post, w, d in conns:
            assert pre == post
            assert w == CURR_WEIGHT
            assert d == DELAY
        for i in range(min(pre_size, post_size)):
            assert len(spikes[i]) == 1
            assert spikes[i][0] > (i % 100)

    def test_pre_same_as_post(self):
        self.do_one_to_one_test(10, 23, 23)

    def test_pre_bigger_than_post(self):
        self.do_one_to_one_test(10, 100, 23)

    def test_post_bigger_than_pre(self):
        self.do_one_to_one_test(10, 23, 100)

    def test_post_bigger_than_pre_cond(self):
        self.do_one_to_one_cond_test(10, 5, 4)

    def test_3d_same(self):
        self.do_one_to_one_nd_test(
            (3, 2, 4), 6 * 8 * 8, sim.Grid3D(6/8, 6/8),
            (3, 2, 4), 6 * 8 * 8, sim.Grid3D(6/8, 6/8))

    def test_2d_different_split(self):
        self.do_one_to_one_nd_test(
            (2, 3), 6 * 9, sim.Grid2D(6 / 9),
            (3, 9), 6 * 9, sim.Grid2D(6 / 9))

    def test_2d_pre_bigger_than_post(self):
        self.do_one_to_one_nd_test(
            (2, 3), 6 * 9, sim.Grid2D(6 / 9),
            (3, 3), 3 * 6, sim.Grid2D(3 / 6))

    def test_2d_post_bigger_than_pre(self):
        self.do_one_to_one_nd_test(
            (2, 3), 6 * 9, sim.Grid2D(6 / 9),
            (3, 3), 3 * 6, sim.Grid2D(3 / 6))

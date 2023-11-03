# Copyright (c) 2023 The University of Manchester
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

SOURCES = 5
DESTINATIONS = 10


class TestFixedProbConnector(BaseTestCase):

    def do_fixed_prob_nd_run(
            self, neurons_per_core_pre, pre_size, pre_shape,
            neurons_per_core_post, post_size, post_shape, prob):
        sim.setup(1.0)
        pre = sim.Population(
            pre_size, sim.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = sim.Population(
            post_size, sim.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)
        proj = sim.Projection(
            pre, post, sim.FixedProbabilityConnector(prob),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        sim.end()

        n_avg = pre_size * post_size * prob
        n_low = max(0, n_avg - (n_avg * 0.2))
        n_high = min(pre_size * post_size, n_avg + (n_avg * 0.2))
        assert n_low <= len(conns) <= n_high

    def do_fixed_prob_nd_run_no_self(
            self, neurons_per_core, size, shape, prob):
        sim.setup(1.0)
        pop = sim.Population(
            size, sim.IF_curr_exp(), structure=shape)
        pop.set_max_atoms_per_core(neurons_per_core)
        proj = sim.Projection(
            pop, pop, sim.FixedProbabilityConnector(
                prob, allow_self_connections=False),
            sim.StaticSynapse(weight=1.0, delay=1.0))
        sim.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        sim.end()

        n_avg = size * size * prob
        n_low = max(0, n_avg - (n_avg * 0.2))
        n_high = min(size * size, n_avg + (n_avg * 0.2))
        assert n_low <= len(conns) <= n_high
        assert all(i != j for i, j in conns)

    def test_fixed_number_1d(self):
        self.do_fixed_prob_nd_run(7, 100, None, 8, 50, None, 0.1)

    def test_fixed_number_3d_to_1d(self):
        self.do_fixed_prob_nd_run(
            (3, 4, 2), 3 * 8 * 8, sim.Grid3D(3 / 8, 3 / 8),
            11, 30, None, 0.11)

    def test_fixed_number_2d_no_self(self):
        self.do_fixed_prob_nd_run_no_self(
            (5, 3), 10 * 15, sim.Grid2D(10 / 15), 0.5)

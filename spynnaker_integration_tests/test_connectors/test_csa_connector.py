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
import csa  # type: ignore[import]
from spinnaker_testbase.base_test_case import BaseTestCase
import pyNN.spiNNaker as p


class CSAConnectorTest(BaseTestCase):

    def do_csa_nd_test(
            self, neurons_per_core_pre, pre_size, pre_shape,
            neurons_per_core_post, post_size, post_shape, cset):
        p.setup(1.0)
        pre = p.Population(
            pre_size, p.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = p.Population(
            post_size, p.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)

        conn = p.CSAConnector(cset)
        proj = p.Projection(
            pre, post, conn, p.StaticSynapse(weight=1.0, delay=1.0))
        p.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        p.end()

        full_cset = numpy.array([(s, t) for (s, t) in csa.cross(
                range(pre_size), range(post_size)) * cset])

        assert numpy.array_equal(numpy.sort(full_cset, axis=0),
                                 numpy.sort(conns, axis=0))
        return conns

    def test_1d_one_to_one(self):
        conns = self.do_csa_nd_test(4, 25, None, 6, 35, None, csa.oneToOne)
        assert all(i == j for (i, j) in conns)

    def test_1d_from_list(self):
        conns = self.do_csa_nd_test(
            4, 10, None, 6, 10, None, [(i, i + 1 % 10) for i in range(10)])
        assert all(j == i + 1 % 10 for (i, j) in conns)

    def test_1d_random(self):
        conns = self.do_csa_nd_test(
            4, 10, None, 6, 10, None, csa.random(0.05))
        assert len(conns) > 0

    def test_1d_block_random(self):
        conns = self.do_csa_nd_test(
            3, 10, None, 4, 10, None,
            csa.block(2, 5) * csa.random(0.5) * csa.random(0.3))
        assert len(conns) > 0

    def test_2d(self):
        self.do_csa_nd_test(
            (2, 6), 12 * 18, p.Grid2D(12 / 18),
            (3, 3), 6 * 12, p.Grid2D(6 / 12), csa.block(3, 1) * csa.full)

    def test_3d_to_1d(self):
        self.do_csa_nd_test(
            (1, 4, 3), 4 * 4 * 6, p.Grid3D(4 / 4, 4 / 6),
            30, 96, None, csa.block(4, 4) * csa.random(0.5))

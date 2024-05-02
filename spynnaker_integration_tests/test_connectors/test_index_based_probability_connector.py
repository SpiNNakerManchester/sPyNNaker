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
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class IndexBasedProbabilityConnectorTest(BaseTestCase):

    def do_index_nd_test(
            self, neurons_per_core_pre, pre_size, pre_shape,
            neurons_per_core_post, post_size, post_shape):
        p.setup(1.0)
        pre = p.Population(
            pre_size, p.IF_curr_exp(), structure=pre_shape)
        pre.set_max_atoms_per_core(neurons_per_core_pre)
        post = p.Population(
            post_size, p.IF_curr_exp(), structure=post_shape)
        post.set_max_atoms_per_core(neurons_per_core_post)

        i_expr = "i != j"
        conn = p.IndexBasedProbabilityConnector(i_expr)
        proj = p.Projection(
            pre, post, conn, p.StaticSynapse(weight=1.0, delay=1.0))
        p.run(0)
        conns = numpy.array(
            [(int(i), int(j)) for i, j in proj.get([], "list")])
        p.end()

        expected_conns = numpy.array([(i, j) for i in range(pre_size)
                                      for j in range(post_size) if i != j])

        assert numpy.array_equal(numpy.sort(expected_conns, axis=1),
                                 numpy.sort(conns, axis=1))

    def test_2d_index(self):
        self.do_index_nd_test(
            (2, 3), 6 * 12, p.Grid2D(6 / 12),
            (4, 1), 8 * 3, p.Grid2D(8 / 3))

    def test_3d_index(self):
        self.do_index_nd_test(
            (2, 3, 5), 6 * 12 * 10, p.Grid3D(6 / 12, 6 / 10),
            (4, 1, 2), 8 * 3 * 4, p.Grid3D(8 / 3, 8 / 4))

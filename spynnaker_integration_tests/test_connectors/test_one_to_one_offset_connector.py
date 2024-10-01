# Copyright (c) 2024 The University of Manchester
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
import pytest
import numpy

from pacman.model.graphs.common.slice import Slice
from spinnaker_testbase import BaseTestCase


class TestOneToOneOffsetConnector(BaseTestCase):

    def check_offset(self):
        timestep = 1.0
        sim.setup(timestep=timestep)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 2)
        pop = sim.Population(11, sim.IF_curr_exp())
        proj_no_wrap = sim.Projection(
            pop, pop, sim.extra_models.OneToOneOffsetConnector(-2, wrap=False),
            synapse_type=sim.StaticSynapse())
        proj_wrap = sim.Projection(
            pop, pop, sim.extra_models.OneToOneOffsetConnector(3, wrap=True),
            synapse_type=sim.StaticSynapse())
        sim.run(0)
        conns_no_wrap = list(proj_no_wrap.get([], format="list"))
        conns_wrap = list(proj_wrap.get([], format="list"))
        sim.end()
        print(conns_wrap)
        print(conns_no_wrap)
        assert len(conns_no_wrap) == 9
        assert len(conns_wrap) == 11
        for i, j in conns_no_wrap:
            assert j == i - 2
        for i, j in conns_wrap:
            assert j == (i + 3) % 11

    def test_offset(self):
        self.runsafe(self.check_offset)

    def check_offset_groups(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)
        pop = sim.Population(12, sim.IF_curr_exp())
        proj_no_wrap = sim.Projection(
            pop, pop, sim.extra_models.OneToOneOffsetConnector(
                4, wrap=False, n_neurons_per_group=6))
        proj_wrap = sim.Projection(
            pop, pop, sim.extra_models.OneToOneOffsetConnector(
                -1, wrap=True, n_neurons_per_group=3))
        sim.run(0)
        conns_no_wrap = list(proj_no_wrap.get([], format="list"))
        conns_wrap = list(proj_wrap.get([], format="list"))
        sim.end()

        assert len(conns_no_wrap) == 4
        assert len(conns_wrap) == 12

        for i, j in conns_no_wrap:
            group_i = i // 6
            group_j = j // 6
            assert group_i == group_j
            assert j == i + 4

        for i, j in conns_wrap:
            group_i = i // 3
            group_j = j // 3
            assert group_i == group_j
            assert j - (group_j * 3) == (i - (group_i * 3) - 1) % 3

    def test_offset_groups(self):
        self.runsafe(self.check_offset_groups)

    def check_offset_offline(self):
        sim.setup(timestep=1)
        pop = sim.Population(11, sim.IF_curr_exp())
        conn_no_wrap = sim.extra_models.OneToOneOffsetConnector(
            offset=-1, wrap=False)
        conn_wrap = sim.extra_models.OneToOneOffsetConnector(
            offset=3, wrap=True)
        proj_wrap = sim.Projection(pop, pop, conn_wrap)
        proj_no_wrap = sim.Projection(pop, pop, conn_no_wrap)
        sim.run(0)
        conns_wrap = list(proj_wrap.get([], format="list"))
        conns_no_wrap = list(proj_no_wrap.get([], format="list"))
        post_vertex_slice = Slice(0, 11)
        post_slices = [post_vertex_slice]
        synapse_type = 0
        synapse_info_no_wrap = proj_no_wrap._synapse_information
        synapse_info_wrap = proj_wrap._synapse_information
        block_no_wrap = conn_no_wrap.create_synaptic_block(
            post_slices, post_vertex_slice, synapse_type, synapse_info_no_wrap)
        block_wrap = conn_wrap.create_synaptic_block(
            post_slices, post_vertex_slice, synapse_type, synapse_info_wrap)
        offline_conns_no_wrap = sorted(
            list([i, j] for (i, j, _w, _d, _typ) in block_no_wrap))
        offline_conns_wrap = sorted(
            list([i, j] for (i, j, _w, _d, _typ) in block_wrap))
        sim.end()
        assert numpy.array_equal(conns_no_wrap, offline_conns_no_wrap)
        assert numpy.array_equal(conns_wrap, offline_conns_wrap)

    def test_offset_offline(self):
        self.runsafe(self.check_offset_offline)

    def check_offset_wrong_number_of_neurons(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(11, sim.IF_curr_exp())
        post = sim.Population(11, sim.IF_curr_exp())
        with pytest.raises(NotImplementedError):
            sim.Projection(
                pre, post, sim.extra_models.OneToOneOffsetConnector(
                    3, False, n_neurons_per_group=3))
        sim.end()

    def test_offset_wrong_number_of_neurons(self):
        self.runsafe(self.check_offset_wrong_number_of_neurons)

    def check_offset_diff_number_of_neurons(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(12, sim.IF_curr_exp())
        post = sim.Population(9, sim.IF_curr_exp())
        with pytest.raises(NotImplementedError):
            sim.Projection(
                pre, post, sim.extra_models.OneToOneOffsetConnector(
                    2, True, n_neurons_per_group=3))
        sim.end()

    def test_offset_diff_number_of_neurons(self):
        self.runsafe(self.check_offset_diff_number_of_neurons)

    def check_offset_wrong_offset(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(12, sim.IF_curr_exp())
        post = sim.Population(12, sim.IF_curr_exp())
        with pytest.raises(ValueError):
            sim.Projection(
                pre, post, sim.extra_models.OneToOneOffsetConnector(
                    12, True, n_neurons_per_group=3))
        sim.end()

    def test_offset_wrong_offset(self):
        self.runsafe(self.check_offset_wrong_offset)

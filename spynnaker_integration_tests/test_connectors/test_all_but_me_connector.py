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
from itertools import permutations
import pytest
import numpy

from pacman.model.graphs.common.slice import Slice
from spinnaker_testbase import BaseTestCase


class TestAllButMeConnector(BaseTestCase):

    def check_all_but_me(self):
        weight = 5.0
        timestep = 1.0
        sim.setup(timestep=timestep)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 2)
        pop = sim.Population(11, sim.IF_curr_exp())
        proj = sim.Projection(
            pop, pop, sim.extra_models.AllButMeConnector(),
            synapse_type=sim.StaticSynapse(weight=weight))
        sim.run(0)
        conns = list(proj.get(["weight", "delay"], format="list"))
        sim.end()
        print(conns)
        # weight if not set in the connector will be the one from the syanpse
        # delay if not set in the synapse will be the timestep
        for index, (i, j) in enumerate(permutations(range(11), 2)):
            assert conns[index] == [i, j, weight, timestep]

    def test_all_but_me(self):
        self.runsafe(self.check_all_but_me)

    def check_all_but_me_groups(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)
        pop = sim.Population(12, sim.IF_curr_exp())
        proj = sim.Projection(pop, pop, sim.extra_models.AllButMeConnector(
            n_neurons_per_group=3))
        sim.run(0)
        conns = list(proj.get([], format="list"))
        sim.end()
        groups = list()
        for group_start in range(0, 12, 3):
            group_end = min(12, group_start + 3)
            neurons_in_group = range(group_start, group_end)
            groups.extend([i, j]
                          for (i, j) in permutations(neurons_in_group, 2))
        print(conns)
        print(groups)
        assert numpy.array_equal(conns, groups)

    def test_all_but_me_groups(self):
        self.runsafe(self.check_all_but_me_groups)

    def check_all_but_me_offline(self):
        sim.setup(timestep=1)
        pop = sim.Population(11, sim.IF_curr_exp())
        conn = sim.extra_models.AllButMeConnector()
        proj = sim.Projection(pop, pop, conn)
        sim.run(0)
        conns = list(proj.get([], format="list"))
        post_vertex_slice = Slice(0, 11)
        post_slices = [post_vertex_slice]
        synapse_type = 0
        synapse_info = proj._synapse_information
        offline_conns = sorted(
            list([i, j] for (i, j, _w, _d, _typ) in conn.create_synaptic_block(
                post_slices, post_vertex_slice, synapse_type, synapse_info)))
        sim.end()
        groups = list([i, j] for (i, j) in permutations(range(11), 2))
        print(conns)
        print(groups)
        print(offline_conns)
        assert numpy.array_equal(conns, groups)
        assert numpy.array_equal(conns, offline_conns)

    def test_all_but_me_offline(self):
        self.runsafe(self.check_all_but_me_offline)

    def check_all_but_me_weights(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(11, sim.IF_curr_exp())
        post = sim.Population(11, sim.IF_curr_exp())
        weights = numpy.arange(0.25, ((11 * 10) + 1) * 0.25, 0.25)
        conn = sim.extra_models.AllButMeConnector(weights=weights)
        # The weight in the synapse_type is ignored it the connector has one
        proj = sim.Projection(pre, post, conn,
                              synapse_type=sim.StaticSynapse(weight=.3))
        sim.run(0)
        conns = list(proj.get(["weight"], format="list"))
        sim.end()
        groups = list(
            [i, j, w] for ((i, j), w) in
            zip(permutations(range(11), 2), weights))
        print(conns)
        print(groups)
        assert numpy.array_equal(conns, groups)

    def test_all_but_me_weights(self):
        self.runsafe(self.check_all_but_me_weights)

    def check_all_but_me_wrong_number_of_neurons(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(11, sim.IF_curr_exp())
        post = sim.Population(11, sim.IF_curr_exp())
        with pytest.raises(NotImplementedError):
            sim.Projection(
                pre, post, sim.extra_models.AllButMeConnector(
                    n_neurons_per_group=3))
        sim.end()

    def test_all_but_me_wrong_number_of_neurons(self):
        self.runsafe(self.check_all_but_me_wrong_number_of_neurons)

    def check_all_but_me_diff_number_of_neurons(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(12, sim.IF_curr_exp())
        post = sim.Population(9, sim.IF_curr_exp())
        with pytest.raises(NotImplementedError):
            sim.Projection(
                pre, post, sim.extra_models.AllButMeConnector(
                    n_neurons_per_group=3))
        sim.end()

    def test_all_but_me_diff_number_of_neurons(self):
        self.runsafe(self.check_all_but_me_diff_number_of_neurons)

    def check_all_but_me_wrong_number_of_weights(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 3)
        pre = sim.Population(12, sim.IF_curr_exp())
        post = sim.Population(12, sim.IF_curr_exp())
        with pytest.raises(ValueError):
            sim.Projection(
                pre, post, sim.extra_models.AllButMeConnector(
                    n_neurons_per_group=3, weights=[10]))
        sim.end()

    def test_all_but_me_wrong_number_of_weights(self):
        self.runsafe(self.check_all_but_me_wrong_number_of_weights)

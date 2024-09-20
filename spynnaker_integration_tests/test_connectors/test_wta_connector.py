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
import numpy
from pacman.model.graphs.common.slice import Slice


def test_wta():
    sim.setup()
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 2)
    pop = sim.Population(11, sim.IF_curr_exp())
    proj = sim.Projection(pop, pop, sim.extra_models.WTAConnector())
    sim.run(0)
    conns = list(proj.get([], format="list"))
    sim.end()
    groups = list([i, j] for (i, j) in permutations(range(11), 2))
    print(conns)
    print(groups)
    assert numpy.array_equal(conns, groups)


def test_wta_groups():
    sim.setup()
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 4)
    pop = sim.Population(11, sim.IF_curr_exp())
    proj = sim.Projection(pop, pop, sim.extra_models.WTAConnector(n_values=3))
    sim.run(0)
    conns = list(proj.get([], format="list"))
    sim.end()
    groups = list()
    for group_start in range(0, 11, 3):
        group_end = min(11, group_start + 3)
        neurons_in_group = range(group_start, group_end)
        groups.extend([i, j] for (i, j) in permutations(neurons_in_group, 2))
    print(conns)
    print(groups)
    assert numpy.array_equal(conns, groups)


def test_wta_offline():
    sim.setup()
    pop = sim.Population(11, sim.IF_curr_exp())
    conn = sim.extra_models.WTAConnector()
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


if __name__ == "__main__":
    test_wta_offline()

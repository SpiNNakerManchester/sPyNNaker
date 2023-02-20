# Copyright (c) 2017 The University of Manchester
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
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as p
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)


def split_structural_without_stdp():
    p.setup(1.0)
    stim = p.Population(1, p.SpikeSourceArray(range(10)), label="stim")

    # These populations should experience formation
    pop = p.Population(
        1, p.IF_curr_exp(), label="pop", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})
    pop_2 = p.Population(
        1, p.IF_curr_exp(), label="pop_2", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})

    # These populations should experience elimination
    pop_3 = p.Population(
        1, p.IF_curr_exp(), label="pop_3", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})
    pop_4 = p.Population(
        1, p.IF_curr_exp(), label="pop_4", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})

    # Formation with last-neuron selection (0 probability elimination)
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), p.StructuralMechanismStatic(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 1.0),
            elimination=p.RandomByWeightElimination(2.0, 0, 0),
            f_rew=1000, initial_weight=2.0, initial_delay=5.0,
            s_max=1, seed=0, weight=0.0, delay=1.0))

    # Formation with random selection (0 probability elimination)
    proj_2 = p.Projection(
        stim, pop_2, p.FromListConnector([]), p.StructuralMechanismStatic(
            partner_selection=p.RandomSelection(),
            formation=p.DistanceDependentFormation([1, 1], 1.0),
            elimination=p.RandomByWeightElimination(4.0, 0, 0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=1, seed=0, weight=0.0, delay=1.0))

    # Elimination with last neuron selection (0 probability formation)
    proj_3 = p.Projection(
        stim, pop_3, p.FromListConnector([(0, 0)]),
        p.StructuralMechanismStatic(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            f_rew=1000, initial_weight=2.0, initial_delay=5.0,
            s_max=1, seed=0, weight=0.0, delay=1.0))

    # Elimination with random selection (0 probability formation)
    proj_4 = p.Projection(
        stim, pop_4, p.FromListConnector([(0, 0)]),
        p.StructuralMechanismStatic(
            partner_selection=p.RandomSelection(),
            formation=p.DistanceDependentFormation([1, 1], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=1, seed=0, weight=0.0, delay=1.0))
    p.run(10)

    # Get the final connections
    conns = list(proj.get(["weight", "delay"], "list"))
    conns_2 = list(proj_2.get(["weight", "delay"], "list"))
    conns_3 = list(proj_3.get(["weight", "delay"], "list"))
    conns_4 = list(proj_4.get(["weight", "delay"], "list"))

    p.end()

    print(conns)
    print(conns_2)
    print(conns_3)
    print(conns_4)

    # These should be formed with specified parameters
    assert len(conns) == 1
    assert tuple(conns[0]) == (0, 0, 2.0, 5.0)
    assert len(conns_2) == 1
    assert tuple(conns_2[0]) == (0, 0, 4.0, 3.0)

    # These should have no connections since eliminated
    assert len(conns_3) == 0
    assert len(conns_4) == 0


class TestStructuralWithoutSTDP(BaseTestCase):

    def test_split_structural_without_stdp(self):
        self.runsafe(split_structural_without_stdp)

# Copyright (c) 2017-2022 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

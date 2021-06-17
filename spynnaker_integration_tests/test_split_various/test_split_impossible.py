# Copyright (c) 2021 The University of Manchester
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
import spynnaker8 as sim
import pytest
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)
from spynnaker.pyNN.exceptions import SynapticConfigurationException


def test_mission_impossible():
    sim.setup(0.1, time_scale_factor=1)

    # Can't do that many neurons and delays together
    sim.Population(128, sim.IF_curr_exp(), additional_parameters={
        "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(
            1, 128, False)})

    with pytest.raises(SynapticConfigurationException):
        sim.run(100)


def test_mission_impossible_2():
    sim.setup(0.1, time_scale_factor=1)

    # Can't do structural on multiple synapse cores
    source = sim.Population(1, sim.SpikeSourcePoisson(rate=10))
    pop = sim.Population(128, sim.IF_curr_exp(), additional_parameters={
        "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(
            2)})

    sim.Projection(source, pop, sim.FromListConnector([]),
                   sim.StructuralMechanismStatic(
                       sim.RandomSelection(), sim.DistanceDependentFormation(),
                       sim.RandomByWeightElimination(0.5)))

    with pytest.raises(SynapticConfigurationException):
        sim.run(100)

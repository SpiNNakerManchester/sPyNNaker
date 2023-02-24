# Copyright (c) 2021 The University of Manchester
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
import pyNN.spiNNaker as sim
import pytest
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)
from spynnaker.pyNN.exceptions import SynapticConfigurationException
from spinnaker_testbase import BaseTestCase


def mission_impossible():
    sim.setup(0.1, time_scale_factor=1)

    # Can't do that many neurons and delays together
    sim.Population(128, sim.IF_curr_exp(), additional_parameters={
        "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(
            1, 128, False)})

    with pytest.raises(SynapticConfigurationException):
        sim.run(100)


def mission_impossible_2():
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


class TestSplitImpossible(BaseTestCase):

    def test_mission_impossible(self):
        self.runsafe(mission_impossible)

    def test_mission_impossible_2(self):
        self.runsafe(mission_impossible_2)

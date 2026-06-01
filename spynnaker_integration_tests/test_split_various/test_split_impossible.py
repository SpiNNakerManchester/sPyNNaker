# Copyright (c) 2021 The University of Manchester
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
from spynnaker.pyNN.exceptions import (
    SynapticConfigurationException, DelayExtensionException)
from spinnaker_testbase import BaseTestCase


def mission_impossible() -> None:
    sim.setup(0.1, time_scale_factor=1)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 128)
    sim.set_number_of_synapse_cores(sim.IF_curr_exp, 1)
    sim.set_allow_delay_extensions(sim.IF_curr_exp, False)

    # Can't do that many neurons and delays together
    pre = sim.Population(1, sim.SpikeSourcePoisson(rate=10))
    post = sim.Population(128, sim.IF_curr_exp())
    sim.Projection(pre, post, sim.OneToOneConnector(),
                   sim.StaticSynapse(weight=5.0, delay=12.8))

    with pytest.raises(DelayExtensionException):
        sim.run(100)


def mission_impossible_2() -> None:
    sim.setup(0.1, time_scale_factor=1)

    # Can't do structural on multiple synapse cores
    source = sim.Population(1, sim.SpikeSourcePoisson(rate=10))
    pop = sim.Population(128, sim.IF_curr_exp(), n_synapse_cores=2)

    sim.Projection(source, pop, sim.FromListConnector([]),
                   sim.StructuralMechanismStatic(
                       sim.RandomSelection(), sim.DistanceDependentFormation(),
                       sim.RandomByWeightElimination(0.5)))

    with pytest.raises(SynapticConfigurationException):
        sim.run(100)


class TestSplitImpossible(BaseTestCase):

    def test_mission_impossible(self) -> None:
        self.runsafe(mission_impossible)

    def test_mission_impossible_2(self) -> None:
        self.runsafe(mission_impossible_2)

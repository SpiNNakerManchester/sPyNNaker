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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
import numpy


class TestSTDPRandomRun(BaseTestCase):
    # Test that reset with STDP and using Random weights results in the
    # same thing being loaded twice, both with data generated off and on the
    # machine

    def do_run(self):
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp(i_offset=5.0), label="pop")
        pop.record("spikes")
        pop_2 = sim.Population(1, sim.IF_curr_exp(), label="pop_2")
        proj = sim.Projection(
            pop, pop_2, sim.AllToAllConnector(),
            sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(),
                weight_dependence=sim.AdditiveWeightDependence(),
                weight=sim.RandomDistribution("uniform", low=0.3, high=0.7)))
        proj_2 = sim.Projection(
            pop, pop_2, sim.OneToOneConnector(),
            sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(),
                weight_dependence=sim.AdditiveWeightDependence(),
                weight=sim.RandomDistribution("uniform", low=0.3, high=0.7)))
        sim.run(100)
        weights_1_1 = proj.get("weight", "list")
        weights_1_2 = proj_2.get("weight", "list")
        spikes_1 = pop.get_data("spikes").segments[0].spiketrains

        sim.reset()
        sim.run(100)
        weights_2_1 = proj.get("weight", "list")
        weights_2_2 = proj_2.get("weight", "list")
        spikes_2 = pop.get_data("spikes").segments[1].spiketrains
        sim.end()

        assert numpy.array_equal(weights_1_1, weights_2_1)
        assert numpy.array_equal(weights_1_2, weights_2_2)
        assert numpy.array_equal(spikes_1, spikes_2)

    def test_do_run(self):
        self.runsafe(self.do_run)

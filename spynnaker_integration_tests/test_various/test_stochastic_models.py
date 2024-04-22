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
from spinnaker_testbase import BaseTestCase


class TestStochasticModels(BaseTestCase):

    def run_stoc_exp(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(100, sim.extra_models.StocExp())
        pop.record("spikes")
        sim.run(1000)
        spikes = pop.get_data("spikes").segments[0].spiketrains
        sim.end()

        # Expected to spike around 10% of the time,
        # but each spike lasts for 10 time-steps, so this allows some
        # margin for error
        for s in spikes:
            print(len(s))
            self.assertTrue(len(s) > 0)
            self.assertTrue(len(s) < 750)

    def run_stoc_exp_stable(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(100, sim.extra_models.StocExpStable())
        pop.record("spikes")
        sim.run(1000)
        spikes = pop.get_data("spikes").segments[0].spiketrains
        sim.end()

        # Expected to spike around 10% of the time, so this allows some
        # margin for error
        for s in spikes:
            self.assertTrue(len(s) > 0)
            self.assertTrue(len(s) < 500)

    def run_stoc_sigma(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(100, sim.extra_models.StocSigma())
        pop.record("spikes")
        sim.run(1000)
        spikes = pop.get_data("spikes").segments[0].spiketrains
        sim.end()

        # Expected to spike around 50% of the time, so this allows some
        # margin for error
        for s in spikes:
            self.assertTrue(len(s) > 0)
            self.assertTrue(len(s) < 750)

    def test_stoc_exp(self):
        self.runsafe(self.run_stoc_exp)

    def test_stoc_exp_stable(self):
        self.runsafe(self.run_stoc_exp_stable)

    def test_stoc_sigma(self):
        self.runsafe(self.run_stoc_sigma)

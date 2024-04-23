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


class TestDeltaModels(BaseTestCase):

    def run_delta_fixed_prob(self):
        sim.setup(timestep=1.0)
        pop = sim.Population(100, sim.extra_models.IFCurrDeltaFixedProb(
            i_offset=2.0, p_thresh=0.5))
        pop.record("spikes")
        sim.run(1000)
        spikes = pop.get_data("spikes").segments[0].spiketrains
        sim.end()

        # Expected to spike around 50% of the time, but allow some margin
        # for error
        for s in spikes:
            self.assertTrue(len(s) > 250)
            self.assertTrue(len(s) < 750)

    def run_delta_trunc(self):
        sim.setup(timestep=1.0)

        test_spikes = sim.Population(100, sim.SpikeSourcePoisson(rate=100))
        pop = sim.Population(100, sim.extra_models.IFTruncDelta(
            i_offset=0.1, v_reset=0.0))
        pop.record("v")
        sim.Projection(test_spikes, pop, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=-1.0),
                       receptor_type="inhibitory")

        sim.run(1000)
        v = pop.get_data("v").segments[0].filter(name="v")
        sim.end()

        # Voltage should not go below 0
        for v_n in v[0]:
            for v_m in v_n:
                assert v_m >= 0.0

    def test_delta_fixed_prob(self):
        self.runsafe(self.run_delta_fixed_prob)

    def test_delta_trunc(self):
        self.runsafe(self.run_delta_trunc)

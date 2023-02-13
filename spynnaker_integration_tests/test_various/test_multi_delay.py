# Copyright (c) 2022-2023 The University of Manchester
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


class TestMultiDelay(BaseTestCase):
    """
    tests the run is split buy auto pause resume
    """

    def test_run(self):
        n_neurons = 70
        sim.setup(timestep=1.0)

        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        input = sim.Population(
            n_neurons, sim.SpikeSourceArray(spike_times=range(0, 3000, 100)),
            label="input")
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=1))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=20))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=40))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=60))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=80))
        pop_1.record(["spikes"])
        sim.run(4000)

        spikes = pop_1.spinnaker_get_data("spikes")
        sim.end()

        self.assertEqual(30*5*n_neurons, len(spikes))

    def more_runs(self):
        self.runsafe(self.more_runs)

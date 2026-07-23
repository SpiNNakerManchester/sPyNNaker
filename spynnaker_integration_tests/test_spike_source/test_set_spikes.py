# Copyright (c) 2017 The University of Manchester
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

class TestSetSpikes(BaseTestCase):

    def do_run(self) -> None:
        n_neurons = 3
        spike_times = [[12, 40], [], [23]]

        assert len(spike_times) == n_neurons

        sim.setup(timestep=1.0)

        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        input_pop = sim.Population(
            n_neurons, sim.SpikeSourceArray(spike_times=[0]), label="input")
        input_proj = sim.Projection(input_pop, pop_1, sim.OneToOneConnector(),
                                    synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1.record(["spikes"])
        input_pop.record("spikes")

        # ... but set spike times here
        for idx in range(n_neurons):
            input_pop[idx].set(spike_times=spike_times[idx])

        sim.run(100)

        in_spikes = input_pop.spinnaker_get_data("spikes").tolist()
        out_spikes = pop_1.spinnaker_get_data("spikes").tolist()
        sim.end()

        self.assertSequenceEqual([[0, 12], [0, 40], [2, 23]], in_spikes)
        self.assertSequenceEqual([[0, 19], [0, 45], [2, 30]], out_spikes)

    def test_run(self) -> None:
        self.runsafe(self.do_run)

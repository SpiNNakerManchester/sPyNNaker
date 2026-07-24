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

        sim.setup(timestep=1.0)

        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        input_pop = sim.Population(
            n_neurons, sim.SpikeSourceArray(), label="input")
        sim.Projection(input_pop, pop_1, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1.record(["spikes"])
        input_pop.record("spikes")
        input_pop.describe()

        sim.run(100)
        in_spikes = input_pop.spinnaker_get_data("spikes").tolist()
        out_spikes = pop_1.spinnaker_get_data("spikes").tolist()
        self.assertEqual(0, len(in_spikes))
        self.assertEqual(0, len(out_spikes))

        input_pop.set(spike_times=[10, 20, 30])
        sim.reset()
        sim.run(100)
        in_spikes = input_pop.spinnaker_get_data("spikes").tolist()
        out_spikes = pop_1.spinnaker_get_data("spikes").tolist()
        self.assertSequenceEqual([
            [0, 10], [0, 20], [0, 30],
            [1, 10], [1, 20], [1, 30],
            [2, 10], [2, 20], [2, 30]], in_spikes)
        self.assertSequenceEqual([
            [0, 17], [0, 24], [0, 33],
            [1, 17], [1, 24], [1, 33],
            [2, 17], [2, 24], [2, 33]], out_spikes)

        # ... but set spike times here
        input_pop.set(spike_times=[])
        spike_times = [[12, 40], [], [23]]
        assert len(spike_times) == n_neurons
        for idx in range(n_neurons):
            input_pop[idx].set(spike_times=spike_times[idx])
        sim.reset()
        sim.run(100)

        in_spikes = input_pop.spinnaker_get_data("spikes").tolist()
        out_spikes = pop_1.spinnaker_get_data("spikes").tolist()
        self.assertSequenceEqual([[0, 12], [0, 40], [2, 23]], in_spikes)
        self.assertSequenceEqual([[0, 19], [0, 45], [2, 30]], out_spikes)

        input_pop.set(spike_times=[])
        with self.assertRaises(NotImplementedError):
            # requires mapping so hard reset required.
            sim.run(100)

        sim.end()


    def test_run(self) -> None:
        self.runsafe(self.do_run)

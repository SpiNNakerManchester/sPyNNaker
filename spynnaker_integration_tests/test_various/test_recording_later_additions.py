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


class TestRecordingLaterAdditions(BaseTestCase):

    def do_simple(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        input_pop = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0, 7]), label="input")

        pop_1 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input_pop, pop_1, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1.record(["spikes", "v"])
        sim.run(10)
        neo = pop_1.get_data(variables=["spikes", "v"])
        spikes = neo.segments[0].spiketrains
        self.assertEqual(
            '<SpikeTrain(array([7.]) * ms, [0.0 ms, 10.0 ms])>',
            repr(spikes[0]))
        v = neo.segments[0].filter(name='v')
        self.assertEqual(1, len(v)) # number of arrays
        self.assertEqual(10, len(v[0]))
        sim.reset()

        pop_2 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input_pop, pop_2, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_2.record(["spikes", "v"])
        sim.run(20)

        neo = pop_1.get_data(variables=["spikes", "v"])
        spikes = neo.segments[0].spiketrains
        self.assertEqual(
            '<SpikeTrain(array([7.]) * ms, [0.0 ms, 10.0 ms])>',
            repr(spikes[0]))
        spikes = neo.segments[1].spiketrains
        self.assertEqual(
            '<SpikeTrain(array([ 7., 15.]) * ms, [0.0 ms, 20.0 ms])>',
            repr(spikes[0]))
        v = neo.segments[0].filter(name='v')
        self.assertEqual(1, len(v)) # number of arrays
        self.assertEqual(10, len(v[0]))
        v = neo.segments[1].filter(name='v')
        self.assertEqual(1, len(v)) # number of arrays
        self.assertEqual(20, len(v[0]))

        sc = pop_1.get_spike_counts()
        self.assertEqual(3, sc)
        pop_1.write_data("test.csv", ["spikes", "v"])
        sim.end()

    def test_simple(self):
        self.runsafe(self.do_simple)

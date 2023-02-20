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


class TestSampling(BaseTestCase):

    def test_thrtytwo(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        pop_1 = sim.Population(40, sim.IF_curr_exp(), label="pop_1")
        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        # A range of 32 was problematic
        # due to the need for one more index to point none recording at
        pop_1[0:32].record(["spikes", "v"])
        simtime = 10
        sim.run(simtime)

        neo = pop_1.get_data(variables=["spikes", "v"])
        # pylint: disable=no-member
        spikes = neo.segments[0].spiketrains
        # Include all the spiketrains as there is no outside index
        self.assertEqual(40, len(spikes))
        for i in range(32):
            self.assertEqual(1, len(spikes[i]))
        for i in range(32, 40):
            self.assertEqual(0, len(spikes[i]))
        v = neo.segments[0].filter(name='v')[0]
        self.assertEqual(32, len(v.channel_index.index))
        self.assertEqual(32, len(v[0]))
        sim.end()

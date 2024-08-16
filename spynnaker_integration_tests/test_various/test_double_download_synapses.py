#!/usr/bin/python

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

from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim


class TestDoubleDownloadSynapses(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0, n_boards_required=1)
        pop = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
        input_pop = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input")
        sim.Projection(input_pop, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1),
                       download_synapses=True)
        sim.Projection(input_pop, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1),
                       download_synapses=True)
        pop.record(["spikes", "v"])
        sim.run(10)

        neo = pop.get_data(variables=["spikes", "v"])
        spikes = neo.segments[0].spiketrains
        print(spikes)
        v = neo.segments[0].filter(name='v')[0]
        print(v)
        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

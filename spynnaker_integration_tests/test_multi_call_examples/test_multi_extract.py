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
from spynnaker.pyNN.utilities import neo_compare
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import check_neuron_data

n_neurons = 20  # number of neurons in each population
neurons_per_core = n_neurons / 2
simtime = 1000


class TestMultiExtract(BaseTestCase):

    def check_data(self, pop, expected_spikes, simtime, early_neo):
        neo = pop.get_data("all")
        spikes = neo.segments[0].spiketrains
        v = neo.segments[0].filter(name="v")[0]
        gsyn_exc = neo.segments[0].filter(name="gsyn_exc")[0]
        for i in range(len(spikes)):
            check_neuron_data(spikes[i], v[:, i], gsyn_exc[:, i],
                              expected_spikes, simtime, pop.label, i)
        neo_compare.compare_blocks(neo, early_neo, same_length=False)

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, neurons_per_core)

        input_spikes = list(range(0, simtime - 100, 10))
        expected_spikes = len(input_spikes)
        input = sim.Population(
            1, sim.SpikeSourceArray(spike_times=input_spikes), label="input")
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1.record(["spikes", "v", "gsyn_exc"])
        sim.run(simtime//2)
        early_neo = pop_1.get_data("all")
        sim.run(simtime//2)
        sim.run(simtime)
        self.check_data(pop_1, expected_spikes, simtime, early_neo)
        sim.end()

    def test_do_run(self):
        self.runsafe(self.do_run)

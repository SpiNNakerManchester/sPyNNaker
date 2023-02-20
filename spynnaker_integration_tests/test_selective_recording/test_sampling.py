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
from spynnaker_integration_tests.scripts import PatternSpiker


class TestSampling(BaseTestCase):

    def medium(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 1000
        spike_rate = 5
        n_neurons = 320
        spike_rec_indexes = list(range(0, 100, 2)) + list(range(100, 200, 3)) \
            + list(range(200, 300, 1)) + list(range(300, 320, 4))
        v_rec_indexes = list(range(0, 100, 1)) + list(range(100, 200, 3)) \
            + list(range(200, 300, 4)) + list(range(300, 320, 2))
        v_rate = 3
        pop = ps.create_population(sim, n_neurons=n_neurons, label="test",
                                   spike_rate=spike_rate,
                                   spike_rec_indexes=spike_rec_indexes,
                                   v_rate=v_rate, v_rec_indexes=v_rec_indexes)
        sim.run(simtime)
        ps.check(pop, simtime,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=False)

    def test_medium(self):
        self.runsafe(self.medium)

    def multirun(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 32
        spike_rate = 5
        spike_rec_indexes = [1, 3, 5, 7, 9, 10]
        v_rec_indexes = [0, 21, 32, 45]
        v_rate = 3
        pop = ps.create_population(sim, n_neurons=32 * 2, label="test",
                                   spike_rate=spike_rate,
                                   spike_rec_indexes=spike_rec_indexes,
                                   v_rate=v_rate, v_rec_indexes=v_rec_indexes)
        sim.run(simtime)
        sim.run(simtime)
        sim.run(simtime)
        ps.check(pop, simtime * 3,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=False)
        ps.check(pop, simtime * 3,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=True)
        sim.end()

    def test_multirun(self):
        self.runsafe(self.multirun)

    def different_views(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 100
        pop = ps.create_population(
            sim, n_neurons=10, v_rec_indexes=[2, 4, 6, 8], label="test")
        sim.run(simtime)
        ps.check(pop, simtime, v_rec_indexes=[2, 3, 4], is_view=True,
                 missing=True)
        sim.end()

    def test_different_views(self):
        self.runsafe(self.different_views)

    def standard(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 100
        pop = ps.create_population(sim, n_neurons=32 * 4, label="test")
        sim.run(simtime)
        ps.check(pop, simtime)
        sim.end()

    def test_standard(self):
        self.runsafe(self.standard)

    def one_core_no_recording(self):
        sim.setup(timestep=1)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)

        pop_1 = sim.Population(10, sim.IF_curr_exp(), label="pop_1")
        input_pop = sim.Population(
            10, sim.SpikeSourceArray(spike_times=[0]), label="input")
        sim.Projection(input_pop, pop_1, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1[0:3].record(["spikes", "v"])
        simtime = 10
        sim.run(simtime)

    def test_one_core_no_recording(self):
        self.runsafe(self.one_core_no_recording)

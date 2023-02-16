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


class TestRecordPacketsPerTimestep(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)

        runtime = 500
        n_neurons = 10

        spike_times = list(n for n in range(0, runtime, 100))
        pop_src = sim.Population(n_neurons, sim.SpikeSourceArray(spike_times),
                                 label="src")
        pop_lif = sim.Population(n_neurons, sim.IF_curr_exp(), label="lif")

        weight = 5
        delay = 5
        sim.Projection(pop_src, pop_lif, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=weight, delay=delay),
                       receptor_type="excitatory")

        pop_lif.record("packets-per-timestep")
        sim.run(runtime)

        pps = pop_lif.get_data('packets-per-timestep')
        pps_array = pps.segments[0].filter(name='packets-per-timestep')[0]

        # Packets at the destination arrive one timestep after src spike_times
        for n in range(runtime):
            if (n - 1) in spike_times:
                assert pps_array[n] == n_neurons
            else:
                assert pps_array[n] == 0

        sim.end()

    def do_multi_run(self):
        sim.setup(timestep=1.0)
        runtime = 500
        n_neurons = 10
        spikegap = 50

        spike_times = list(n for n in range(0, runtime, spikegap))
        pop_src = sim.Population(n_neurons, sim.SpikeSourceArray(spike_times),
                                 label="src")

        pop_lif = sim.Population(n_neurons, sim.IF_curr_exp(), label="lif")

        weight = 5
        delay = 5

        # define the projection
        sim.Projection(pop_src, pop_lif, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=weight, delay=delay),
                       receptor_type="excitatory")

        pop_lif.record("all")

        sim.run(runtime//2)
        sim.run(runtime//2)

        pps = pop_lif.get_data()

        totalpackets = sum(
            pps.segments[0].filter(name='packets-per-timestep')[0])

        assert totalpackets == n_neurons * (runtime // spikegap)

        sim.end()

    def do_run_with_reset(self):
        sim.setup(timestep=1.0)
        runtime = 500
        n_neurons = 10
        spikegap = 50

        spike_times = list(n for n in range(0, runtime, spikegap))
        pop_src = sim.Population(n_neurons, sim.SpikeSourceArray(spike_times),
                                 label="src")

        pop_lif = sim.Population(n_neurons, sim.IF_curr_exp(), label="lif")

        weight = 5
        delay = 5

        # define the projection
        sim.Projection(pop_src, pop_lif, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=weight, delay=delay),
                       receptor_type="excitatory")

        pop_lif.record("all")

        sim.run(runtime//2)

        # add another population to ensure a hard reset
        sim.Population(n_neurons, sim.IF_curr_exp(), label="lif2")
        sim.reset()

        sim.run(runtime//2)

        pps = pop_lif.get_data()

        totalpackets = sum(
            pps.segments[0].filter(name='packets-per-timestep')[0]) + sum(
                pps.segments[1].filter(name='packets-per-timestep')[0])

        assert totalpackets == n_neurons * (runtime // spikegap)

        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

    def test_multi_run(self):
        self.runsafe(self.do_multi_run)

    def test_run_with_reset(self):
        self.runsafe(self.do_run_with_reset)

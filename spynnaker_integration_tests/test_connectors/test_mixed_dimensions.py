# Copyright (c) 2025 The University of Manchester
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


class SmallWorldConnectorFixedTest(BaseTestCase):

    def do_run(self):

        sim.setup(timestep=1.0)
        n_atoms = 6 * 6
        # Parameters
        runtime = n_atoms + 100

        # SpikeInjector
        spike_times = list()
        for i in range(n_atoms):
            spike_times.append([i, i + 10, i + 20, i + 30])
        inj_pop = sim.Population(
            n_atoms, sim.SpikeSourceArray(spike_times=spike_times),
            label='inputSpikes')

        # Network population
        grid_structure = sim.Grid2D(dx=2, dy=3, x0=0.0, y0=0.0)
        small_world = sim.Population(
            6 * 6, sim.IF_curr_exp(), structure=grid_structure,
            label="small_world")
        small_world.set_max_atoms_per_core((2, 2))
        small_world.record(['spikes'])

        # Injector projection
        sim.Projection(inj_pop, small_world, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))

        after_pop = sim.Population(n_atoms, sim.IF_curr_exp(), label="after")
        after_pop.set_max_atoms_per_core(5)
        after_pop.record(["spikes"])

        sim.Projection(small_world, after_pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        after_pop.record(["spikes"])

        sim.run(runtime)

        small_spikes = small_world.get_data('spikes').segments[0].spiketrains
        after_spikes = after_pop.get_data('spikes').segments[0].spiketrains

        sim.end()

        for n in range(n_atoms):
            self.assertEqual(4, len(small_spikes[n]))
            self.assertEqual(4, len(after_spikes[n]))
            # Make sure each neurons spikes 1 after the one before
            for i in range(4):
                self.assertEqual(small_spikes[0][i].magnitude + n,
                                 small_spikes[n][i].magnitude)
                self.assertEqual(after_spikes[0][i].magnitude + n,
                                 after_spikes[n][i].magnitude)

    def test_mixed(self):
        self.runsafe(self.do_run)
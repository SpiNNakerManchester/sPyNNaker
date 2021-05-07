# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import spynnaker8 as sim
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
                assert(pps_array[n] == n_neurons)
            else:
                assert(pps_array[n] == 0)

        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

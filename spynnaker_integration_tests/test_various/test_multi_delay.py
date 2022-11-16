# Copyright (c) 2022 The University of Manchester
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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestMultiDelay(BaseTestCase):
    """
    tests the run is split buy auto pause resume
    """

    def test_run(self):
        n_neurons = 70
        sim.setup(timestep=1.0)

        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        input = sim.Population(
            n_neurons, sim.SpikeSourceArray(spike_times=range(0, 3000, 100)),
            label="input")
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=1))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=20))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=40))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=60))
        sim.Projection(
            input, pop_1, sim.OneToOneConnector(),
            synapse_type=sim.StaticSynapse(weight=5, delay=80))
        pop_1.record(["spikes"])
        sim.run(4000)

        spikes = pop_1.spinnaker_get_data("spikes")
        sim.end()

        self.assertEqual(30*5*n_neurons, len(spikes))

    def more_runs(self):
        self.runsafe(self.more_runs)

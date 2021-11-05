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
from spynnaker_integration_tests.scripts import check_neuron_data

n_neurons = 20  # number of neurons in each population
neurons_per_core = n_neurons / 2
simtime = 200


class TestResetNewInput(BaseTestCase):

    def check_data(self, pop, expected_spikes, simtime, segments):
        neo = pop.get_data("all")
        for segment in segments:
            spikes = neo.segments[segment].spiketrains
            v = neo.segments[segment].filter(name="v")[0]
            gsyn_exc = neo.segments[segment].filter(name="gsyn_exc")[0]
            for i in range(len(spikes)):
                check_neuron_data(spikes[i], v[:, i], gsyn_exc[:, i],
                                  expected_spikes,
                                  simtime, pop.label, i)

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, neurons_per_core)

        input_spikes = list(range(0, simtime - 50, 10))
        input = sim.Population(
            1, sim.SpikeSourceArray(spike_times=input_spikes), label="input")
        pop_1 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1.record(["spikes", "v", "gsyn_exc"])
        sim.run(simtime)
        sim.reset()
        pop_2 = sim.Population(n_neurons, sim.IF_curr_exp(), label="pop_2")
        pop_2.record(["spikes", "v", "gsyn_exc"])
        sim.Projection(input, pop_2, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        sim.run(simtime)
        self.check_data(pop_1, len(input_spikes), simtime, [0, 1])
        self.check_data(pop_2, len(input_spikes), simtime, [1])
        sim.end()

    def test_do_run(self):
        self.runsafe(self.do_run)

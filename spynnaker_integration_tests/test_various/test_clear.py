# Copyright (c) 2017-2020 The University of Manchester
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


class TestClearData(BaseTestCase):

    def make_rewires(self):
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)
        stim = sim.Population(9, sim.SpikeSourceArray(range(10)), label="stim")

        # These populations should experience elimination
        pop = sim.Population(9, sim.IF_curr_exp(), label="pop_1")

        # Elimination with random selection (0 probability formation)
        sim.Projection(
            stim, pop, sim.AllToAllConnector(),
            sim.StructuralMechanismStatic(
                partner_selection=sim.RandomSelection(),
                formation=sim.DistanceDependentFormation([3, 3], 0.0),
                elimination=sim.RandomByWeightElimination(4.0, 1.0, 1.0),
                f_rew=1000, initial_weight=4.0, initial_delay=3.0,
                s_max=9, seed=0, weight=0.0, delay=1.0))

        pop.record("rewiring")
        sim.run(10)
        neo = pop.get_data("rewiring", clear=True)
        elimination_events = neo.segments[0].events[1]
        self.assertEqual(len(elimination_events), 10)
        sim.run(10)
        neo = pop.get_data("rewiring", clear=True)
        elimination_events = neo.segments[0].events[1]
        self.assertEqual(len(elimination_events), 10)

        sim.end()

    def do_simple(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        pop_1 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
        input_pop = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0, 10, 20]), label="input")
        sim.Projection(input_pop, pop_1, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop_1.record(["spikes", "v"])
        sim.run(20)
        neo = pop_1.get_data(variables=["spikes", "v"], clear=True)
        spikes = neo.segments[0].spiketrains
        self.assertEqual(
            '<SpikeTrain(array([ 7., 14.]) * ms, [0.0 ms, 20.0 ms])>',
            repr(spikes[0]))
        v = neo.segments[0].filter(name='v')[0]
        self.assertEqual(20, v.size)
        sim.run(10)
        neo = pop_1.get_data(variables=["spikes", "v"], clear=True)
        spikes = neo.segments[0].spiketrains
        self.assertEqual(
            '<SpikeTrain(array([23.]) * ms, [20.0 ms, 30.0 ms])>',
            repr(spikes[0]))
        v = neo.segments[0].filter(name='v')[0]
        self.assertEqual(10, v.size)
        sim.end()

    def test_rewires(self):
        self.runsafe(self.make_rewires)

    def test_simple(self):
        self.runsafe(self.do_simple)

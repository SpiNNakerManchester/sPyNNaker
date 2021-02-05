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
from pacman.model.constraints.placer_constraints import (
    RadialPlacementFromChipConstraint)
from p8_integration_tests.base_test_case import BaseTestCase


class TestConstraint(BaseTestCase):

    def test_radial_some(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 50)

        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        pop_1.set_constraint(RadialPlacementFromChipConstraint(1, 1))
        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        simtime = 10
        sim.run(simtime)
        placements = self.get_placements("pop_1")
        sim.end()
        self.assertEqual(4, len(placements))
        for [x, y, _] in placements:
            self.assertEqual("1", x)
            self.assertEqual("1", y)

    def test_radial_many(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 10)

        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        pop_1.set_constraint(RadialPlacementFromChipConstraint(1, 1))
        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        simtime = 10
        sim.run(simtime)
        placements = self.get_placements("pop_1")
        sim.end()
        self.assertEqual(20, len(placements))
        count = 0
        for [x, y, _] in placements:
            if x == "1" and y == "1":
                count += 1
        self.assertGreater(count, 10)

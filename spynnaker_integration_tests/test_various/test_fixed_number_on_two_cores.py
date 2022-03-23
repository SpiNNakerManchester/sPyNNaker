#!/usr/bin/python

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

from spinnaker_testbase import BaseTestCase
import spynnaker8 as sim


class FixNumberOnTwoCoresCase(BaseTestCase):

    def do_run(self):
        n_neurons = 100
        weights = 0.5
        delays = 17.0
        n_pre = 10

        sim.setup(timestep=1.0, min_delay=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 50)

        p1 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop1')
        p2 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop2')
        connector = sim.FixedNumberPreConnector(n_pre)
        projection = sim.Projection(p1, p2, connector,
                                    synapse_type=sim.StaticSynapse(
                                        weight=weights, delay=delays))
        sim.run(10)
        weight_list = projection.get(["weight"], "list")
        sim.end()

        length = len(weight_list)
        self.assertEqual(n_neurons*n_pre, length)

    def test_run(self):
        self.runsafe(self.do_run)

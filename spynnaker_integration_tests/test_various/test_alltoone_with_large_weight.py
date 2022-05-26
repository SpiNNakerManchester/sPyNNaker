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
import pyNN.spiNNaker as sim


class AllToOneWithLargeWeightCase(BaseTestCase):

    def do_run(self):
        sources = 700
        destinations = 1
        weights = 50.0
        delays = 1

        sim.setup(timestep=1.0, min_delay=1.0)

        p1 = sim.Population(sources, sim.IF_curr_exp, {}, label='pop1')
        p2 = sim.Population(destinations, sim.IF_curr_exp, {}, label='pop2')
        connector = sim.AllToAllConnector()
        projection = sim.Projection(p1, p2, connector,
                                    synapse_type=sim.StaticSynapse(
                                        weight=weights, delay=delays))
        sim.run(10)
        weight_list = projection.get(["weight"], "list")
        sim.end()

        weight_sum = sum(weight[2] for weight in weight_list)
        # 50.0 is not exactly representable so specify a relevant tolerance
        self.assertAlmostEqual(weight_sum, sources * weights,
                               delta=sources*0.05)

    def test_run(self):
        self.runsafe(self.do_run)

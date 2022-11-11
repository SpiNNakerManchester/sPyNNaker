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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestOneToOneConnector(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def check_weights(self, projection, sources, destinations):
        weights = projection.get(["weight"], "list")
        last_source = -1
        for (source, destination, _) in weights:
            self.assertNotEqual(source, last_source)
            last_source = source
            self.assertEqual(source, destination)
            self.assertLess(source, sources)
            self.assertLess(destination, sources)
        self.assertEqual(len(weights), min(sources, destinations))

    def check_other_connect(self, sources, destinations):
        sim.setup(1.0)
        pop1 = sim.Population(sources, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(destinations, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.OneToOneConnector(), synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, sources, destinations)
        sim.end()

    def test_same(self):
        self.check_other_connect(5, 5)

    # Does not work on VM
    # def test_less_sources(self):
    #    self.check_other_connect(5, 10)

    # Does not work on VM
    # def test_less_destinations(self):
    #    self.check_other_connect(10, 5)

    def test_many(self):
        self.check_other_connect(500, 500)

    def test_get_before_run(self):
        sim.setup(1.0)
        pop1 = sim.Population(3, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(3, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.OneToOneConnector(),
            synapse_type=synapse_type)
        weights = projection.get(["weight"], "list")
        sim.run(0)
        self.assertEqual(3, len(weights))
        sim.end()

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
from spynnaker.pyNN.config_setup import unittest_setup

WEIGHT = 5
DELAY = 2


class TestIndexBasedProbabilityConnector(BaseTestCase):

    def setUp(self):
        unittest_setup()

    def check_weights(self, projection, n, expression, allow_self_connections):
        weights = projection.get(["weight"], "list")
        pairs = [(s, d) for (s, d, _) in weights]
        must_count = 0
        maybe_count = 0
        for i in range(n):
            for j in range(n):
                if not allow_self_connections and (i == j):
                    self.assertNotIn((i, j), pairs)
                    continue
                kwargs = {"i": i, "j": j}
                prob = eval(expression, kwargs)
                if prob == 1:
                    self.assertIn((i, j), pairs)
                    must_count += 1
                elif prob == 0:
                    self.assertNotIn((i, j), pairs)
                else:
                    maybe_count += 1
        # Check at least one maybe connected
        self.assertLessEqual(len(weights), must_count + maybe_count)
        # Check not all the maybes connected
        self.assertGreaterEqual(len(weights), must_count)

    def check_connect(self, n, expression, allow_self_connections):
        n = 6
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 10)
        pop1 = sim.Population(
            n, sim.SpikeSourceArray(spike_times=[0]), label="input")
        pop2 = sim.Population(n, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=2)

        projection = sim.Projection(
            pop1, pop2, sim.IndexBasedProbabilityConnector(
                expression, allow_self_connections=allow_self_connections),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(projection, n, expression, allow_self_connections)
        sim.end()

    def test_self(self):
        self.check_connect(
            n=6, expression="(i+j)%3*0.5", allow_self_connections=True)

    def test_other(self):
        self.check_connect(
            n=6, expression="(i+j)%3*0.5", allow_self_connections=False)

    def test_big(self):
        self.check_connect(
            n=60, expression="(i+j)%3*0.5", allow_self_connections=True)

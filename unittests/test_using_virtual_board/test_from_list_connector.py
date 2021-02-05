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
from p8_integration_tests.base_test_case import BaseTestCase

WEIGHT = 5
DELAY = 2


class TestFromListConnector(BaseTestCase):

    def check_weights(
            self, projection, aslist, w_index, d_index, sources, destinations):
        from_pro = projection.get(["weight", "delay"], "list")
        aslist.sort()
        as_index = 0
        for (source, dest, weight, delay) in from_pro:
            from_as = aslist[as_index]
            while from_as[0] >= sources:
                as_index += 1
                from_as = aslist[as_index]
            while from_as[1] >= destinations:
                as_index += 1
                from_as = aslist[as_index]
            self.assertEqual(from_as[0], source)
            self.assertEqual(from_as[1], dest)
            if w_index:
                self.assertAlmostEqual(from_as[w_index], weight, 4)
            else:
                self.assertEqual(WEIGHT, weight)
            if d_index:
                self.assertAlmostEqual(from_as[d_index], delay, 4)
            else:
                self.assertEqual(DELAY, delay)
            as_index += 1
        while as_index < len(aslist):
            from_as = aslist[as_index]
            assert(from_as[0] >= sources or from_as[1] >= destinations)
            as_index += 1

    def check_other_connect(
            self, aslist, column_names=None, w_index=2, d_index=3, sources=6,
            destinations=8):
        sim.setup(1.0)
        pop1 = sim.Population(sources, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(destinations, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=WEIGHT, delay=DELAY)
        projection = sim.Projection(
            pop1, pop2, sim.FromListConnector(
                aslist, column_names=column_names),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(
            projection, aslist, w_index, d_index, sources, destinations)
        sim.end()

    def test_simple(self):
        as_list = [
            (0, 0, 0.1, 10),
            (3, 0, 0.2, 11),
            (2, 3, 0.3, 12),
            (5, 1, 0.4, 13),
            (0, 1, 0.5, 14),
        ]
        self.check_other_connect(as_list)

    def test_list_too_big(self):
        as_list = [
            (0, 0, 0.1, 10),
            (13, 0, 0.2, 11),
            (2, 13, 0.3, 12),
            (5, 1, 0.4, 13),
            (0, 1, 0.5, 14),
        ]
        self.check_other_connect(as_list)

    def test_no_delays(self):
        as_list = [
            (0, 0, 0.1),
            (3, 0, 0.2),
            (2, 3, 0.3),
            (5, 1, 0.4),
            (0, 1, 0.5),
        ]
        self.check_other_connect(
            as_list, column_names=["weight"], d_index=None)

    def test_no_weight(self):
        as_list = [
            (0, 0, 10),
            (3, 0, 11),
            (2, 3, 12),
            (5, 1, 13),
            (0, 1, 14),
        ]
        self.check_other_connect(
            as_list, column_names=["delay"], d_index=2, w_index=None)

    def test_invert(self):
        as_list = [
            (0, 0, 10, 0.1),
            (3, 0, 11, 0.2),
            (2, 3, 12, 0.3),
            (5, 1, 13, 0.4),
            (0, 1, 14, 0.5),
        ]
        self.check_other_connect(
            as_list, column_names=["delay", "weight"], w_index=3, d_index=2)

    def test_big(self):
        sources = 200
        destinations = 300
        aslist = []
        for s in range(sources):
            for d in range(destinations):
                aslist.append((s, d, 5, 2))

        self.check_other_connect(
            aslist, column_names=None, w_index=2, d_index=3, sources=sources,
            destinations=destinations)

    def test_get_before_run(self):
        sim.setup(1.0)
        pop1 = sim.Population(3, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(3, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=5, delay=1)
        projection = sim.Projection(
            pop1, pop2, sim.FromListConnector([[0, 0]]),
            synapse_type=synapse_type)
        weights = projection.get(["weight"], "list")
        sim.run(0)
        self.assertEqual(1, len(weights))
        sim.end()

    def test_using_static_synapse_singles(self):
        sim.setup(timestep=1.0)
        input = sim.Population(2, sim.SpikeSourceArray([0]), label="input")
        pop = sim.Population(2, sim.IF_curr_exp(), label="pop")
        as_list = [(0, 0), (1, 1)]
        conn = sim.Projection(input, pop, sim.FromListConnector(as_list),
                              sim.StaticSynapse(weight=0.7, delay=3))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        target = [(0, 0, 0.7, 3), (1, 1, 0.7, 3)]
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(weights[i][j], target[i][j], places=3)

    def test_using_half_static_synapse_singles(self):
        sim.setup(timestep=1.0)
        input = sim.Population(2, sim.SpikeSourceArray([0]), label="input")
        pop = sim.Population(2, sim.IF_curr_exp(), label="pop")
        as_list = [(0, 0, 0.7), (1, 1, 0.3)]
        conn = sim.Projection(input, pop, sim.FromListConnector(
            as_list, column_names=["weight"]),
                              sim.StaticSynapse(weight=0.6, delay=3))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        sim.end()
        target = [(0, 0, 0.7, 3), (1, 1, 0.3, 3)]
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(weights[i][j], target[i][j], places=3)

    def test_using_static_synapse_doubles(self):
        sim.setup(timestep=1.0)
        input = sim.Population(2, sim.SpikeSourceArray([0]), label="input")
        pop = sim.Population(2, sim.IF_curr_exp(), label="pop")
        as_list = [(0, 0), (1, 1)]
        conn = sim.Projection(input, pop, sim.FromListConnector(as_list),
                              sim.StaticSynapse(weight=[0.7, 0.3],
                                                delay=[3, 33]))
        sim.run(1)
        weights = conn.get(['weight', 'delay'], 'list')
        target = [(0, 0, 0.7, 3), (1, 1, 0.3, 33)]
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(weights[i][j], target[i][j], places=3)

        sim.end()

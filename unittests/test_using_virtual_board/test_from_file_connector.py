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

import os
import numpy
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
import tempfile

WEIGHT = 5
DELAY = 2


class TestFromFileConnector(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def check_weights(
            self, projection, aslist, w_index, d_index, sources, destinations):
        from_pro = list(projection.get(["weight", "delay"], "list"))
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
                self.assertAlmostEqual(from_as[w_index], weight, 3)
            else:
                self.assertAlmostEqual(WEIGHT, weight, 3)
            if d_index:
                self.assertAlmostEqual(from_as[d_index], delay, 3)
            else:
                self.assertAlmostEqual(DELAY, delay, 3)
            as_index += 1
        while as_index < len(aslist):
            from_as = aslist[as_index]
            assert from_as[0] >= sources or from_as[1] >= destinations
            as_index += 1

    def check_other_connect(
            self, aslist, header=None, w_index=2, d_index=3, sources=6,
            destinations=8):
        _, name = tempfile.mkstemp(".temp")
        if header:
            numpy.savetxt(name, aslist, header=header)
        else:
            numpy.savetxt(name, aslist)

        sim.setup(1.0)
        pop1 = sim.Population(sources, sim.IF_curr_exp(), label="pop1")
        pop2 = sim.Population(destinations, sim.IF_curr_exp(), label="pop2")
        synapse_type = sim.StaticSynapse(weight=WEIGHT, delay=DELAY)
        projection = sim.Projection(
            pop1, pop2, sim.FromFileConnector(name),
            synapse_type=synapse_type)
        sim.run(0)
        self.check_weights(
            projection, aslist, w_index, d_index, sources, destinations)
        sim.end()
        try:
            os.unlink(name)
        except OSError:
            pass

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
            as_list, header='columns = ["i", "j", "weight"]', d_index=None)

    def test_no_weight(self):
        as_list = [
            (0, 0, 10),
            (3, 0, 11),
            (2, 3, 12),
            (5, 1, 13),
            (0, 1, 14),
        ]
        self.check_other_connect(
            as_list, header='columns = ["i", "j", "delay"]', d_index=2,
            w_index=None)

    def test_invert(self):
        as_list = [
            (0, 0, 10, 0.1),
            (3, 0, 11, 0.2),
            (2, 3, 12, 0.3),
            (5, 1, 13, 0.4),
            (0, 1, 14, 0.5),
        ]
        self.check_other_connect(
            as_list, header='columns = ["i", "j", "delay", "weight"]',
            w_index=3, d_index=2)

    def test_big(self):
        sources = 200
        destinations = 300
        aslist = []
        for s in range(sources):
            for d in range(destinations):
                aslist.append((s, d, 5, 2))

        self.check_other_connect(
            aslist, header=None, w_index=2, d_index=3, sources=sources,
            destinations=destinations)

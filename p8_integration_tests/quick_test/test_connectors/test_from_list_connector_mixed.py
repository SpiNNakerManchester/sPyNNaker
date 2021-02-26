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


class TestFromListConnectorMixed(BaseTestCase):

    def do_run(self):
        sim.setup(1.0)
        pre = sim.Population(2, sim.IF_curr_exp())
        post = sim.Population(2, sim.IF_curr_exp())
        nrng = sim.NumpyRNG(seed=1)

        # Test case where weights are in list and delays given by random dist
        list1 = [(0, 0, 2.1), (0, 1, 2.6), (1, 1, 3.2)]
        proj1 = sim.Projection(
            pre, post, sim.FromListConnector(list1, column_names=["weight"]),
            sim.StaticSynapse(
                weight=0.5,
                delay=sim.RandomDistribution('uniform', [1, 10], rng=nrng)))

        # Test case where delays are in list and weights given by random dist
        list2 = [(0, 0, 2), (0, 1, 6), (1, 1, 3)]
        proj2 = sim.Projection(
            pre, post, sim.FromListConnector(list2, column_names=["delay"]),
            sim.StaticSynapse(
                weight=sim.RandomDistribution('uniform', [1.5, 3.5], rng=nrng),
                delay=4))

        sim.run(1)
        conns1 = proj1.get(["weight", "delay"], "list")
        conns2 = proj2.get(["weight", "delay"], "list")
        sim.end()

        target1 = [(0, 0, 2.1, 8), (0, 1, 2.6, 6), (1, 1, 3.2, 4)]
        target2 = [(0, 0, 1.7864, 2), (0, 1, 2.0823, 6), (1, 1, 2.4995, 3)]

        # assertAlmostEqual doesn't work on lists, so loop required
        for i in range(3):
            for j in range(2):
                self.assertAlmostEqual(
                    conns1[i][j+2], target1[i][j+2], places=3)
                self.assertAlmostEqual(
                    conns2[i][j+2], target2[i][j+2], places=3)

    def test_from_list_connector_mixed(self):
        self.runsafe(self.do_run)

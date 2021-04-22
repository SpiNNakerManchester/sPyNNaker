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
from spynnaker_integration_tests.scripts import PatternSpiker


class TestSampling(BaseTestCase):

    def medium(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 1000
        spike_rate = 5
        n_neurons = 320
        spike_rec_indexes = list(range(0, 100, 2)) + list(range(100, 200, 3)) \
            + list(range(200, 300, 1)) + list(range(300, 320, 4))
        v_rec_indexes = list(range(0, 100, 1)) + list(range(100, 200, 3)) \
            + list(range(200, 300, 4)) + list(range(300, 320, 2))
        v_rate = 3
        pop = ps.create_population(sim, n_neurons=n_neurons, label="test",
                                   spike_rate=spike_rate,
                                   spike_rec_indexes=spike_rec_indexes,
                                   v_rate=v_rate, v_rec_indexes=v_rec_indexes)
        sim.run(simtime)
        ps.check(pop, simtime,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=False)

    def test_medium(self):
        self.runsafe(self.medium)

    def multirun(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 32
        spike_rate = 5
        spike_rec_indexes = [1, 3, 5, 7, 9, 10]
        v_rec_indexes = [0, 21, 32, 45]
        v_rate = 3
        pop = ps.create_population(sim, n_neurons=32 * 2, label="test",
                                   spike_rate=spike_rate,
                                   spike_rec_indexes=spike_rec_indexes,
                                   v_rate=v_rate, v_rec_indexes=v_rec_indexes)
        sim.run(simtime)
        sim.run(simtime)
        sim.run(simtime)
        ps.check(pop, simtime * 3,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=False)
        ps.check(pop, simtime * 3,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=True)
        sim.end()

    def test_multirun(self):
        self.runsafe(self.multirun)

    def different_views(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 100
        pop = ps.create_population(
            sim, n_neurons=10, v_rec_indexes=[2, 4, 6, 8], label="test")
        sim.run(simtime)
        ps.check(pop, simtime, v_rec_indexes=[2, 3, 4], is_view=True,
                 missing=True)
        sim.end()

    def test_different_views(self):
        self.runsafe(self.different_views)

    def standard(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 100
        pop = ps.create_population(sim, n_neurons=32 * 4, label="test")
        sim.run(simtime)
        ps.check(pop, simtime)
        sim.end()

    def test_standard(self):
        self.runsafe(self.standard)

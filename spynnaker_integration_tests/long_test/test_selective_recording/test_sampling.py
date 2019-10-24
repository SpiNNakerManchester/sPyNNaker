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

import spynnaker as sim
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.patternSpiker import PatternSpiker


class TestSampling(BaseTestCase):

    def big(self):
        ps = PatternSpiker()
        sim.setup(timestep=1)
        simtime = 10000
        spike_rate = 5
        n_neurons = 3200
        spike_rec_indexes = list(range(0, 1000, 2))\
            + list(range(1000, 2000, 3)) \
            + list(range(2000, 3000, 1)) \
            + list(range(3000, 3200, 4))
        v_rec_indexes = list(range(0, 1000, 1))\
            + list(range(1000, 2000, 3)) \
            + list(range(2000, 3000, 4)) \
            + list(range(3000, 3200, 2))
        v_rate = 3
        pop = ps.create_population(sim, n_neurons=n_neurons, label="test",
                                   spike_rate=spike_rate,
                                   spike_rec_indexes=spike_rec_indexes,
                                   v_rate=v_rate, v_rec_indexes=v_rec_indexes)
        sim.run(simtime)
        ps.check(pop, simtime,
                 spike_rate=spike_rate, spike_rec_indexes=spike_rec_indexes,
                 v_rate=v_rate, v_rec_indexes=v_rec_indexes, is_view=False)

    def test_big(self):
        self.runsafe(self.big)

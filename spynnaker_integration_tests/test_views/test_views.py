# Copyright (c) 2017-2022 The University of Manchester
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

import numpy
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestViews(BaseTestCase):

    def set_with_views(self):
        sim.setup(1.0)
        pop = sim.Population(5, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop[2:4].set(i_offset=2.0)
        pop[1, 3].initialize(v=-60)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        v1 = pop.spinnaker_get_data('v')
        sim.end()
        expected = [
            -65., -64.02465820, -63.09686279, -62.21432495, -61.37481689,
            -60., -59.26849365, -58.57263184, -57.91070557, -57.28106689,
            -65., -63.04931641, -61.19375610, -59.42868042, -57.74966431,
            -60., -58.29315186, -56.66952515, -55.12509155, -53.65597534,
            -65., -64.02465820, -63.09686279, -62.21432495, -61.37481689]
        assert numpy.allclose(v1[:, 2], expected)

    def test_set_with_views(self):
        self.runsafe(self.set_with_views)

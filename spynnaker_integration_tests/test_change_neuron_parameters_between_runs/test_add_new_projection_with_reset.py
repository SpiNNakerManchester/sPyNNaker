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

import spynnaker8 as p
from spinnaker_testbase import BaseTestCase


class TestAddNewProjectionWithReset(BaseTestCase):

    def projection_with_reset(self):
        p.setup(1.0)

        inp = p.Population(1, p.IF_curr_exp(), label="input")
        layer = p.Population(1, p.IF_curr_exp(), label="layer")
        output = p.Population(1, p.IF_curr_exp(), label="output")

        p.Projection(inp, layer, p.AllToAllConnector(),
                     p.StaticSynapse(weight=5, delay=2))

        p.run(100)

        layer_to_output = p.Projection(layer, output, p.AllToAllConnector(),
                                       p.StaticSynapse(weight=4, delay=10))

        p.reset()

        p.run(100)

        weights_delays_out = layer_to_output.get(["weight", "delay"], "list")

        p.end()

        assert weights_delays_out[0][2] == 4.0

    def test_projection_with_reset(self):
        self.runsafe(self.projection_with_reset)

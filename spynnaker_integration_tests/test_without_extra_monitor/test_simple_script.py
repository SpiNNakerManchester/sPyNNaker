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


class TestSimpleScript(BaseTestCase):

    def simple_script(self):
        # A simple script that should work whatever we do, but only if the
        # SDRAM is worked out correctly!
        p.setup(1.0)
        src = p.Population(1, p.SpikeSourceArray([50, 150]), label="input_pop")
        pop = p.Population(1, p.IF_curr_exp(), label="neuron")
        p.Projection(
            src, pop, p.OneToOneConnector(),
            synapse_type=p.StaticSynapse(weight=1.0))
        src.record('spikes')
        pop.record("all")
        p.run(200)
        p.end()

    def test_simple_script(self):
        self.runsafe(self.simple_script)

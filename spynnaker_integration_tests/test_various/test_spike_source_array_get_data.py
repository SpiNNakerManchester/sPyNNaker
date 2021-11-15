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


class TestSpikeSourceArrayGetData(BaseTestCase):

    def do_run(self):
        p.setup(timestep=1, min_delay=1)

        population = p.Population(1, p.SpikeSourceArray(spike_times=[[0]]),
                                  label='inputSSA_1')

        population.record("all")

        p.run(30)
        population.get_data("all")
        p.end()

    def test_run(self):
        self.runsafe(self.do_run)

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

from pyNN.random import RandomDistribution
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary
import spynnaker8 as p
from spinnaker_testbase import BaseTestCase


class TestRanged(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_uniform(self):
        # Need to do setup to get a pynn version
        p.setup(10)
        rd = SpynnakerRangeDictionary(10)
        rd["a"] = RandomDistribution("uniform", parameters_pos=[-65.0, -55.0])
        ranges = rd["a"].get_ranges()
        assert 10 == len(ranges)

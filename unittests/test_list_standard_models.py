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

import unittest
import pyNN.spiNNaker as sim


class TestListStandardModules(unittest.TestCase):

    # NO unittest_setup() to make sure call works before setup

    def test_check_list(self):
        results = sim.list_standard_models()
        self.assertIn('IF_cond_exp', results)
        self.assertIn('Izhikevich', results)
        self.assertIn('SpikeSourceArray', results)
        self.assertIn('SpikeSourcePoisson', results)

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
import unittest
from spinn_utilities.config_holder import run_config_checks
from spynnaker.pyNN.config_setup import unittest_setup


class TestCfgChecker(unittest.TestCase):

    def setUp(self):
        unittest_setup()

    def test_config_checks(self):
        unittests = os.path.dirname(__file__)
        parent = os.path.dirname(unittests)
        spynnaker = os.path.join(parent, "spynnaker")
        spy8 = os.path.join(parent, "spynnaker8")
        spynnaker_it = os.path.join(parent, "spynnaker_integration_tests")
        run_config_checks(
            directories=[spynnaker, spy8, spynnaker_it, unittests])

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

from spinn_front_end_common.utilities.exceptions import ConfigurationException
from p8_integration_tests.base_test_case import BaseTestCase
import spynnaker8 as sim


class TestDoNotAllowViolate(BaseTestCase):
    """
    Tests that running too fast needs to be specifically allowed
    """

    def test_do_not_allow_violate(self):
        with self.assertRaises(ConfigurationException):
            sim.setup()   # remember pynn default is 0.1

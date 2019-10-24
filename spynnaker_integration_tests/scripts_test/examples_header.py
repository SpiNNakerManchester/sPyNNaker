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
from p8_integration_tests.scripts_test.script_checker import ScriptChecker


class TestExamples(ScriptChecker):
    """
    test the introlabs
    """
    def setUp(self):
        super(TestExamples, self).setUp()
        examples_tests_dir = os.path.dirname(__file__)
        spynnaker_integration_tests_dir = os.path.dirname(examples_tests_dir)
        spynnaker_dir = os.path.dirname(spynnaker_integration_tests_dir)
        self._introlab_dir = os.path.join(spynnaker_dir, "PyNN8Examples")
        # Jenkins appears to place "PyNN8Examples" here
        if not os.path.exists(self._introlab_dir):
            parent_dir = os.path.dirname(spynnaker_dir)

            self._introlab_dir = os.path.join(parent_dir, "PyNN8Examples")

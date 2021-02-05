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

from p8_integration_tests.scripts_test.script_checker import ScriptChecker
import os
import sys


class TestNewModelTemplates(ScriptChecker):

    def test_my_example(self):
        self.runsafe(self.my_example)

    def my_example(self):
        tests_dir = os.path.dirname(__file__)
        p8_integration_tests_dir = os.path.dirname(tests_dir)
        spynnaker8_dir = os.path.dirname(p8_integration_tests_dir)
        template_dir = os.path.join(
            spynnaker8_dir, "sPyNNaker8NewModelTemplate")
        if not os.path.exists(template_dir):
            parent_dir = os.path.dirname(spynnaker8_dir)
            template_dir = os.path.join(
                parent_dir, "sPyNNaker8NewModelTemplate")
        # Get the examples sub directory
        template_dir = os.path.join(template_dir, "examples")
        sys.path.append(template_dir)
        example_script = os.path.join(
            template_dir, "my_example.py")
        self.check_script(example_script, False)

    def test_my_semd_example(self):
        self.runsafe(self.my_semd_example)

    def my_semd_example(self):
        tests_dir = os.path.dirname(__file__)
        p8_integration_tests_dir = os.path.dirname(tests_dir)
        spynnaker8_dir = os.path.dirname(p8_integration_tests_dir)
        template_dir = os.path.join(
            spynnaker8_dir, "sPyNNaker8NewModelTemplate")
        if not os.path.exists(template_dir):
            parent_dir = os.path.dirname(spynnaker8_dir)
            template_dir = os.path.join(
                parent_dir, "sPyNNaker8NewModelTemplate")
        # Get the examples sub directory
        template_dir = os.path.join(template_dir, "examples")
        sys.path.append(template_dir)
        example_script = os.path.join(
            template_dir, "my_sEMD_example.py")
        self.check_script(example_script, False)

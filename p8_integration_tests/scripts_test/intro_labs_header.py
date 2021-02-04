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


class TestIntroLabs(ScriptChecker):
    """
    test the introlabs
    """
    def setUp(self):
        super(TestIntroLabs, self).setUp()
        introllab_tests_dir = os.path.dirname(__file__)
        p8_integration_tests_dir = os.path.dirname(introllab_tests_dir)
        spynnaker8_dir = os.path.dirname(p8_integration_tests_dir)
        self._introlab_dir = os.path.join(spynnaker8_dir, "IntroLab")
        # Jenkins appears to place Intorlabs here
        if not os.path.exists(self._introlab_dir):
            parent_dir = os.path.dirname(spynnaker8_dir)
            self._introlab_dir = os.path.join(parent_dir, "IntroLab")

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
import matplotlib.pyplot as plt
from spinn_front_end_common.utilities import globals_variables
from p8_integration_tests.base_test_case import BaseTestCase


class TestScripts(BaseTestCase):
    """
    test the introlabs
    """
    def setUp(self):
        super(TestScripts, self).setUp()
        introllab_tests_dir = os.path.dirname(__file__)
        unittest_dir = os.path.dirname(introllab_tests_dir)
        spynnaker8_dir = os.path.dirname(unittest_dir)
        self._introlab_dir = os.path.join(spynnaker8_dir, "IntroLab")
        # Jenkins appears to place Introlabs here otherwise keep looking
        if not os.path.exists(self._introlab_dir):
            parent_dir = os.path.dirname(spynnaker8_dir)
            self._introlab_dir = os.path.join(parent_dir, "IntroLab")

    def mockshow(self):
        self._show = True

    def check_script(self, script):
        self._show = False
        plt.show = self.mockshow
        from runpy import run_path
        run_path(script)
        assert self._show
        self.report(script, "scrpits_ran_successfully")

    def check_directory(self, path):
        directory = os.path.join(self._introlab_dir, path)
        for a_script in os.listdir(directory):
            if a_script.endswith(".py") and a_script != "__init__.py":
                globals_variables.unset_simulator()
                script = os.path.join(directory, a_script)
                try:
                    self.check_script(script)
                except Exception:
                    print("Error on {}".format(script))
                    raise

    def test_learning(self):
        self.check_directory("learning")

    def test_balanced_random(self):
        self.check_directory("balanced_random")

    def test_synfire(self):
        self.check_directory("synfire")


if __name__ == '__main__':
    unittest.main()

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

import io
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
        examples_tests_dir = os.path.dirname(__file__)
        unittest_dir = os.path.dirname(examples_tests_dir)
        spynnaker8_dir = os.path.dirname(unittest_dir)
        self._introlab_dir = os.path.join(spynnaker8_dir, "PyNN8Examples")
        # Jenkins appears to place "PyNN8Examples" here otherwise keep looking
        if not os.path.exists(self._introlab_dir):
            parent_dir = os.path.dirname(spynnaker8_dir)
            self._introlab_dir = os.path.join(parent_dir, "PyNN8Examples")

    def mockshow(self):
        self._show = True

    def check_script(self, script):
        from runpy import run_path
        run_path(script)
        self.report(script, "scripts_ran_successfully")

    def check_plotting_script(self, script):
        self._show = False
        plt.show = self.mockshow
        self.check_script(script)
        assert self._show

    def check_directory(self, path, skips=(), broken=()):
        directory = os.path.join(self._introlab_dir, path)
        for a_script in os.listdir(directory):
            if a_script.endswith(".py") and a_script != "__init__.py":
                if a_script in skips:
                    continue
                script = os.path.join(directory, a_script)
                try:
                    globals_variables.unset_simulator()
                    with io.open(script, encoding="latin_1") as f:
                        plotting = "import matplotlib.pyplot" in f.read()
                    if plotting:
                        self.check_plotting_script(script)
                    else:
                        self.check_script(script)
                except Exception as ex:  # pylint: disable=broad-except
                    if "virtual machine" in str(ex):
                        self.report(script, "scripts_fails_because_on_vm")
                    elif "'ConnectionHolder'" in str(ex):
                        self.report(script, "scripts_fails_because_on_vm")
                    elif a_script in broken:
                        self.report(
                            script, "scripts_skipped_with_unknown_issues")
                    else:
                        print("Error on {}".format(script))
                        raise

    def examples(self):
        self.check_directory(
            "examples", broken=["synfire_if_curr_exp_large_array.py"])

    def test_examples(self):
        self.runsafe(self.examples)

    def test_extra_models_examples(self):
        self.check_directory("examples/extra_models_examples")

    def test_external_devices_examples(self):
        self.check_directory(
            "examples/external_devices_examples",
            skips=["pushbot_ethernet_example.py"])


if __name__ == '__main__':
    unittest.main()

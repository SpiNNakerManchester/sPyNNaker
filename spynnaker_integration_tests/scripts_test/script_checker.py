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

from spynnaker_integration_tests.base_test_case import BaseTestCase
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E401


class ScriptChecker(BaseTestCase):

    def mockshow(self):
        self._show = True

    def check_script(self, script, broken):
        plotting = "import matplotlib.pyplot" in open(script).read()
        if plotting:
            self._show = False
            plt.show = self.mockshow
        from runpy import run_path
        try:
            run_path(script)
            self.report(script, "scripts_ran_successfully")
        except Exception as ex:
            if broken:
                self.report(
                    script, "scripts_skipped_with_unkown_issues")
            else:
                print("Error on {}".format(script))
                raise ex

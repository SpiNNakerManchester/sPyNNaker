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

import time
from spynnaker_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.manyBoards import ManyBoards


class TestPythonSimple(BaseTestCase):

    def do_run(self):
        me = ManyBoards()
        t_before = time.time()
        sim = me.do_run(n_boards=2, n_neurons=50, simtime=300)
        t_after_machine = time.time()
        me.check_all_data()
        t_after_check = time.time()
        results = self.get_run_time_of_BufferExtractor()
        self.report(
            results, "python_simple_n_boards=2_n_neurons=50_simtime=300")
        self.report(
            "machine run time was: {} seconds\n".format(
                t_after_machine-t_before),
            "python_simple_n_boards=2_n_neurons=50_simtime=300")
        self.report(
            "total run time was: {} seconds\n".format(t_after_check-t_before),
            "python_simple_n_boards=2_n_neurons=50_simtime=300")
        sim.end()

    def test_do_run(self):
        self.runsafe(self.do_run)

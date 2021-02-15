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

"""
Synfirechain-like example
"""

# spynnaker imports
import os
from neo.io import PickleIO
import unittest
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner
from spynnaker.pyNN.utilities import neo_compare

n_neurons = 200  # number of neurons in each population
runtime = 500
current_file_path = os.path.dirname(os.path.abspath(__file__))
current_v_file_path = os.path.join(current_file_path, "v.pickle")
max_delay = 14
timestep = 1
neurons_per_core = n_neurons/2
delay = 1.7
synfire_run = SynfireRunner()


class TestPrintVoltage(BaseTestCase):
    """
    tests the printing of print v given a simulation
    """

    def test_print_voltage(self):
        """
        test that tests the printing of v from a pre determined recording
        :return:
        """
        synfire_run.do_run(n_neurons, max_delay=max_delay, time_step=timestep,
                           neurons_per_core=neurons_per_core, delay=delay,
                           run_times=[runtime], v_path=current_v_file_path)
        v_read = synfire_run.get_output_pop_voltage_neo()

        io = PickleIO(filename=current_v_file_path)
        v_saved = io.read()[0]
        neo_compare.compare_blocks(v_read, v_saved)
        os.remove(current_v_file_path)


if __name__ == '__main__':
    unittest.main()

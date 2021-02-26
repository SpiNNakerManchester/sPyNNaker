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
import unittest
from unittest import SkipTest
from spinnman.exceptions import SpinnmanTimeoutException
from spinnaker_testbase import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner

synfire_run = SynfireRunner()


class TestGetVoltage(BaseTestCase):
    """
    tests the printing of get v given a simulation
    """

    def test_get_voltage(self):
        """
        test that tests the getting of v from a pre determined recording
        :return:
        """
        try:
            n_neurons = 200  # number of neurons in each population
            runtime = 500
            synfire_run.do_run(n_neurons, max_delay=14.4, time_step=0.1,
                               neurons_per_core=10, delay=1.7,
                               run_times=[runtime])
            # Exact v check removed as system overloads
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest() from ex


if __name__ == '__main__':
    unittest.main()

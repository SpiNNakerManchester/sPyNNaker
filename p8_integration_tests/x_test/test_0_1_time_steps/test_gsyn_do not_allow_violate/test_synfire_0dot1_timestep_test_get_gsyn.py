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
# general imports
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from p8_integration_tests.scripts.synfire_run import SynfireRunner
from p8_integration_tests.base_test_case import BaseTestCase

n_neurons = 10  # number of neurons in each population
runtime = 50
synfire_run = SynfireRunner()


class TestGsyn(BaseTestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_get_gsyn(self):
        with self.assertRaises(ConfigurationException):
            synfire_run.do_run(n_neurons, max_delay=14.4, time_step=0.1,
                               neurons_per_core=5, delay=1.7,
                               run_times=[runtime])


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, max_delay=14.4, time_step=0.1,
                       neurons_per_core=5, delay=1.7, run_times=[runtime])

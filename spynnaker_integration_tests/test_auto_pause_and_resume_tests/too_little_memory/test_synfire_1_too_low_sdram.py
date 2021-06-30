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
import pytest
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner
from pacman.exceptions import PacmanException

n_neurons = 200  # number of neurons in each population
runtime = 3000
neurons_per_core = 1
synfire_run = SynfireRunner()


class TestTooLow(BaseTestCase):
    """
    tests the run fails due to too small ram
    """

    def test_too_low(self):
        with pytest.raises(PacmanException):
            synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                               run_times=[runtime])


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=[runtime])

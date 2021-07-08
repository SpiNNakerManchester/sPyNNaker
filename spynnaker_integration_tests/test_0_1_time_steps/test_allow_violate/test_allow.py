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

from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner
import spynnaker.spike_checker as spike_checker
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest

n_neurons = 10  # number of neurons in each population
runtime = 50
synfire_run = SynfireRunner()


class TestAllow(BaseTestCase):
    """
    Tests the running of a silumation at faster than real time.
    Success criteria.
        1. Run without errors
        2. Synfire like spike pattern
    """

    def allow(self):
        try:
            synfire_run.do_run(
                n_neurons, time_step=0.1,
                neurons_per_core=5, delay=1.7, run_times=[runtime])

            spikes = synfire_run.get_output_pop_spikes_numpy()
            # no check of spikes length as the system overloads
            spike_checker.synfire_spike_checker(spikes, n_neurons)
            # no check of gsyn as the system overloads
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest() from ex

    def test_allow(self):
        self.runsafe(self.allow)

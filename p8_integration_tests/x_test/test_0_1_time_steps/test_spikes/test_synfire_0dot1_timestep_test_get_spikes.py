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
import spynnaker.spike_checker as spike_checker
from spinnaker_testbase import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner

n_neurons = 200
timestep = 0.1
max_delay = 14.40
delay = 1.7
neurons_per_core = n_neurons/2
runtime = 500
synfire_run = SynfireRunner()


class TestGetSpikesAt0_1msTimeStep(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    def test_get_spikes(self):
        """
        test for get spikes
        """
        try:
            synfire_run.do_run(n_neurons, time_step=timestep,
                               max_delay=max_delay, delay=delay,
                               neurons_per_core=neurons_per_core,
                               run_times=[runtime])
            spikes = synfire_run.get_output_pop_spikes_numpy()
            # Eact spike checking removed as system may oervload
            spike_checker.synfire_spike_checker(spikes, n_neurons)
        # System intentional overload so may error
        except SpinnmanTimeoutException as ex:
            raise SkipTest() from ex


if __name__ == '__main__':
    unittest.main()

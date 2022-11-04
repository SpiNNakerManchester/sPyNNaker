# Copyright (c) 2020 The University of Manchester
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
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts.synfire_runner import SynfireRunner

n_neurons = 200  # number of neurons in each population
runtime = 6000
delay = 100
synfire_run = SynfireRunner()


class TestLongDelay(BaseTestCase):
    """
    tests the run is split buy auto pause resume
    """

    def test_run(self):
        synfire_run.do_run(n_neurons, delay=delay, run_times=[runtime])
        spikes = synfire_run.get_output_pop_spikes_numpy()

        self.assertEqual(59, len(spikes))

    def more_runs(self):
        self.runsafe(self.more_runs)

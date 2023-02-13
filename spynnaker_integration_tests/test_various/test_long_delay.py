# Copyright (c) 2020-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

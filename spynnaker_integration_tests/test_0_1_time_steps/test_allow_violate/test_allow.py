# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner
from spynnaker.pyNN.data import SpynnakerDataView
import spynnaker.spike_checker as spike_checker
from spinnman.exceptions import SpinnmanTimeoutException

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
            SpynnakerDataView.raise_skiptest(parent=ex)

    def test_allow(self):
        self.runsafe(self.allow)

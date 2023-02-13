# Copyright (c) 2017-2023 The University of Manchester
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
from testfixtures import LogCapture
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 200  # number of neurons in each population
runtime = 3000
neurons_per_core = 55
synfire_run = SynfireRunner()


class TestVeryLow(BaseTestCase):
    """
    tests the run is split buy auto pause resume
    """

    def more_runs(self):
        with LogCapture() as lc:
            synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                               run_times=[runtime])
            spikes = synfire_run.get_output_pop_spikes_numpy()
            # CB Currently eight but could change
            # Needs to be larger than 1000 timesteps version
            self.assert_logs_messages(
                lc.records, "*** Running simulation... ***", 'INFO', 2,
                allow_more=True)

        self.assertEqual(158, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        synfire_run.get_output_pop_gsyn_exc_numpy()
        synfire_run.get_output_pop_voltage_numpy()

    def test_more_runs(self):
        self.runsafe(self.more_runs)


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=[runtime])
    gsyn = synfire_run.get_output_pop_gsyn_exc_numpy()
    v = synfire_run.get_output_pop_voltage_numpy()
    spikes = synfire_run.get_output_pop_spikes_numpy()

    print(len(spikes))
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v)
    plot_utils.heat_plot(gsyn)

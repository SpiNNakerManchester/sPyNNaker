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
from testfixtures import LogCapture
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 200  # number of neurons in each population
runtime = 3000
neurons_per_core = int(n_neurons / 2)
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
                lc.records, "*** Running simulation... ***", 'INFO', 1)

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

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
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner

nNeurons = 200  # number of neurons in each population
neurons_per_core = 10
delay = 17
run_times = [5000]
get_weights = True
synfire_run = SynfireRunner()


class SynfireIfCurr_exp(BaseTestCase):

    def test_run(self):
        synfire_run.do_run(nNeurons, neurons_per_core=neurons_per_core,
                           delay=delay, run_times=run_times,
                           get_weights=get_weights)
        spikes = synfire_run.get_output_pop_spikes_numpy()
        weights = synfire_run.get_weights()

        self.assertEqual(263, len(spikes))
        self.assertEqual(200, len(weights))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, neurons_per_core=neurons_per_core,
                       delay=delay, run_times=run_times,
                       get_weights=get_weights)
    spikes = synfire_run.get_output_pop_spikes_numpy()
    weights = synfire_run.get_weights()

    print(len(spikes))
    print(len(weights))
    plot_utils.plot_spikes(spikes)

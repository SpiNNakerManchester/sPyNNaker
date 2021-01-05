#!/usr/bin/python

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

nNeurons = 1600  # number of neurons in each population
run_times = [5000]
record_v = False
record_gsyn = False
synfire_run = SynfireRunner()


class Synfire1600n10pc10chipsWithNoDelaysSpikeRecording(BaseTestCase):

    def test_run(self):
        self.assert_not_spin_three()
        synfire_run.do_run(nNeurons, run_times=run_times, record_v=record_v,
                           record_gsyn_exc=record_gsyn,
                           record_gsyn_inh=record_gsyn)
        spikes = synfire_run.get_output_pop_spikes_numpy()

        self.assertEqual(263, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons)


if __name__ == '__main__':
    synfire_run.do_run(nNeurons, run_times=run_times, record_v=record_v,
                       record_gsyn_exc=record_gsyn,
                       record_gsyn_inh=record_gsyn)
    spikes = synfire_run.get_output_pop_spikes_numpy()

    print(len(spikes))
    plot_utils.plot_spikes(spikes)
    # v and gysn are None

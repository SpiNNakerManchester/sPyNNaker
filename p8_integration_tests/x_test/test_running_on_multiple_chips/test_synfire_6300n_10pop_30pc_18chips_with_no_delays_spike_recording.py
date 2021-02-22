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
import p8_integration_tests.scripts.synfire_npop_run as synfire_npop_run

nNeurons = 630  # number of neurons in each population
runtime = 5000
n_pops = 10
neurons_per_core = 30


class Synfire6300n10pop30pc18chipsNoDelaysSpikeRrecording(BaseTestCase):

    def test_run(self):
        self.assert_not_spin_three()
        results = synfire_npop_run.do_run(nNeurons, n_pops=n_pops,
                                          neurons_per_core=neurons_per_core,
                                          runtime=runtime)
        spikes = results
        self.assertEqual(1666, len(spikes))
        spike_checker.synfire_spike_checker(spikes, nNeurons * n_pops)


if __name__ == '__main__':
    nNeurons = 10  # number of neurons in each population
    results = synfire_npop_run.do_run(nNeurons, n_pops=n_pops,
                                      neurons_per_core=neurons_per_core,
                                      runtime=runtime)
    spikes = results
    print(len(spikes))
    plot_utils.plot_spikes(spikes)

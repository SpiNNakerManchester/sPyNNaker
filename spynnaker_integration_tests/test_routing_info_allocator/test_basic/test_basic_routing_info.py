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
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import do_synfire_npop

n_neurons = 10  # number of neurons in each population
n_pops = 630


class TestBasicRoutingInfo(BaseTestCase):

    def test_run(self):
        results = do_synfire_npop(
            n_neurons, n_pops=n_pops, neurons_per_core=n_neurons)
        spikes = results
        self.assertAlmostEqual(8335, len(spikes), delta=10)


if __name__ == '__main__':
    results = do_synfire_npop(
        n_neurons, n_pops=n_pops, neurons_per_core=n_neurons)
    spikes = results
    print(len(spikes))
    plot_utils.plot_spikes(spikes)

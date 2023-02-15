#!/usr/bin/python

# Copyright (c) 2017 The University of Manchester
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
import spynnaker.plot_utils as plot_utils
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import do_synfire_npop

n_neurons = 10  # number of neurons in each population
n_pops = 630


class TestZonedRoutingInfo(BaseTestCase):

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

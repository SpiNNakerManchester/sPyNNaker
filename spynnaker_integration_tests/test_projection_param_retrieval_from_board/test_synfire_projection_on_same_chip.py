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

import numpy
from spinnaker_testbase import BaseTestCase
from spynnaker_integration_tests.scripts import SynfireRunner

n_neurons = 20  # number of neurons in each population
runtimes = [0, 100]  # The zero uis to read data before a run
neurons_per_core = None
weight_to_spike = 1.0
delay = 1
placement_constraint = (0, 0)
get_weights = True
get_delays = True


class SynfireProjectionOnSameChip(BaseTestCase):

    def get_before_and_after(self):
        synfire_run = SynfireRunner()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           weight_to_spike=weight_to_spike, delay=delay,
                           placement_constraint=placement_constraint,
                           run_times=runtimes, get_weights=get_weights,
                           get_delays=get_delays)
        weights = synfire_run.get_weights()
        self.assertEqual(n_neurons, len(weights[0]))
        self.assertEqual(n_neurons, len(weights[1]))
        self.assertTrue(numpy.allclose(weights[0][0][2], weights[1][0][2]))

        delays = synfire_run.get_delay()
        self.assertEqual(n_neurons, len(delays[0]))
        self.assertEqual(n_neurons, len(delays[1]))
        self.assertTrue(numpy.allclose(delays[0][0][2], delays[1][0][2]))

    def test_get_before_and_after(self):
        self.runsafe(self.get_before_and_after)


if __name__ == '__main__':
    synfire_run = SynfireRunner()
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       weight_to_spike=weight_to_spike, delay=delay,
                       placement_constraint=placement_constraint,
                       run_times=runtimes, get_weights=get_weights,
                       get_delays=get_delays)
    weights = synfire_run.get_weights()
    delays = synfire_run.get_delay()
    print("weights[0]")
    print(weights[0])
    print(weights[0].shape)
    print("weights[1]")
    print(weights[1])
    print(weights[1].shape)
    print("delays[0]")
    print(delays[0])
    print(delays[0].shape)
    print("delays[1]")
    print(delays[1])
    print(delays[1].shape)

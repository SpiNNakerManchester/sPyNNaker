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

    def get_before_and_after(self) -> None:
        synfire_run = SynfireRunner()
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           weight_to_spike=weight_to_spike, delay=delay,
                           placement_constraint=placement_constraint,
                           run_times=runtimes, get_weights=get_weights,
                           get_delays=get_delays)
        weights = synfire_run.get_weights()
        self.assertEqual(n_neurons, len(weights[0]))
        self.assertEqual(n_neurons, len(weights[1]))
        w0 = weights[0][0]
        assert isinstance(w0, list)
        w1 = weights[1][0]
        assert isinstance(w1, list)
        self.assertEqual(w0[2], w1[2])

        delays = synfire_run.get_delay()
        self.assertEqual(n_neurons, len(delays[0]))
        self.assertEqual(n_neurons, len(delays[1]))
        d0 = delays[0][0]
        assert isinstance(d0, list)
        d1 = delays[1][0]
        assert isinstance(d1, list)
        self.assertEqual(d0[2], d1[2])

    def test_get_before_and_after(self) -> None:
        self.runsafe(self.get_before_and_after)

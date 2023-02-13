#!/usr/bin/python

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

from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim


class FixNumberOnTwoCoresCase(BaseTestCase):

    def do_run(self):
        n_neurons = 100
        weights = 0.5
        delays = 17.0
        n_pre = 10

        sim.setup(timestep=1.0, min_delay=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 50)

        p1 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop1')
        p2 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop2')
        connector = sim.FixedNumberPreConnector(n_pre)
        projection = sim.Projection(p1, p2, connector,
                                    synapse_type=sim.StaticSynapse(
                                        weight=weights, delay=delays))
        sim.run(10)
        weight_list = projection.get(["weight"], "list")
        sim.end()

        length = len(weight_list)
        self.assertEqual(n_neurons*n_pre, length)

    def test_run(self):
        self.runsafe(self.do_run)

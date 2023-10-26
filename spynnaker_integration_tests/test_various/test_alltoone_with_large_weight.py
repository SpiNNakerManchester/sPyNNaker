#!/usr/bin/python

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

from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim


class AllToOneWithLargeWeightCase(BaseTestCase):

    def do_run(self):
        sources = 700
        destinations = 1
        weights = 50.0
        delays = 1

        sim.setup(timestep=1.0, min_delay=1.0)

        p1 = sim.Population(sources, sim.IF_curr_exp, {}, label='pop1')
        p2 = sim.Population(destinations, sim.IF_curr_exp, {}, label='pop2')
        connector = sim.AllToAllConnector()
        projection = sim.Projection(p1, p2, connector,
                                    synapse_type=sim.StaticSynapse(
                                        weight=weights, delay=delays))
        sim.run(10)
        weight_list = projection.get(["weight"], "list")
        sim.end()

        weight_sum = sum(weight[2] for weight in weight_list)
        # 50.0 is not exactly representable so specify a relevant tolerance
        self.assertAlmostEqual(weight_sum, sources * weights,
                               delta=sources*0.05)

    def test_run(self):
        self.runsafe(self.do_run)

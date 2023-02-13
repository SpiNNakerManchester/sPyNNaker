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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestUseProjectionGetInFromList(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)

        n_neurons = 10
        weights = 0.5
        delays = 7
        n_pre = 2

        p1 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop1_1')
        p2 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop1_2')

        connector_pre = sim.FixedNumberPreConnector(n_pre)

        proj_pre = sim.Projection(p1, p2, connector_pre,
                                  synapse_type=sim.StaticSynapse(
                                      weight=weights, delay=delays))

        sim.run(10)

        weights_delays_pre = proj_pre.get(["weight", "delay"], "list")

        sim.end()

        sim.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)

        p11 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop2_1')
        p22 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop2_2')

        fromlist_conn = sim.FromListConnector(weights_delays_pre)

        proj_new = sim.Projection(p11, p22, fromlist_conn)

        sim.run(10)

        weights_delays_out = proj_new.get(["weight", "delay"], "list")

        sim.end()

        self.assertCountEqual(weights_delays_pre, weights_delays_out)

    def test_use_projection_get_in_from_list(self):
        self.runsafe(self.do_run)

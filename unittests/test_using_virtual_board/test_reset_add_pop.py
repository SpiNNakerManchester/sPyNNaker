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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestResetAdd(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def testReset_add(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 1)

        input = sim.Population(
            1, sim.SpikeSourceArray(spike_times=[0]), label="input")
        pop_1 = sim.Population(2, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        sim.run(10)
        sim.Population(2, sim.IF_curr_exp(), label="pop_2")
        with self.assertRaises(NotImplementedError):
            sim.run(10)

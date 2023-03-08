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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spinn_front_end_common.utilities.exceptions import ConfigurationException


class SynfireExtractingSpikesWhenNothingSetToRecorded(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_cause_error(self):
        with self.assertRaises(ConfigurationException):
            sim.setup(timestep=1.0)
            sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

            pop_1 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
            input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                                   label="input")
            sim.Projection(input, pop_1, sim.OneToOneConnector(),
                           synapse_type=sim.StaticSynapse(weight=5, delay=1))
            simtime = 10
            sim.run(simtime)

            pop_1.get_data(variables=["spikes"])

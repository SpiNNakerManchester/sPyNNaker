
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


class TestPopulation(BaseTestCase):

    def test_model_fail_to_set_neuron_param_random_distribution(self):
        n_neurons = 5
        range_low = -70
        range_high = -50
        value = sim.RandomDistribution('uniform', (range_low, range_high))
        label = "pop_1"
        sim.setup(timestep=1.0)
        model = sim.IF_curr_exp(i_offset=value)
        pop_1 = sim.Population(n_neurons, model, label=label)
        sim.run(0)
        values = pop_1.get('i_offset')
        for value in values:
            self.assertGreater(value, range_low)
            self.assertLess(value, range_high)
        sim.end()

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

import random
from spinnaker_testbase import BaseTestCase
import numpy
import pyNN.spiNNaker as sim


class MyTestCase(BaseTestCase):

    def recording_1_element(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 200

        boxed_array = numpy.zeros(shape=(0, 2))
        spike_array = list()
        for neuron_id in range(0, n_neurons):
            spike_array.append(list())
            for counter in range(0, 50):
                random_time = random.randint(0, 4999)
                boxed_array = numpy.append(
                    boxed_array, [[neuron_id, random_time]], axis=0)
                spike_array[neuron_id].append(random_time)
        spike_array_params = {'spike_times': spike_array}
        pop1 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop_1')
        pop1.record("all")
        input = sim.Population(n_neurons, sim.SpikeSourceArray,
                               spike_array_params, label='inputSpikes_1')
        input.record("spikes")

        sim.Projection(input, pop1,  sim.OneToOneConnector())

        sim.run(5000)

        spike_array_spikes = input.spinnaker_get_data("spikes")
        boxed_array = boxed_array[numpy.lexsort((boxed_array[:, 1],
                                                 boxed_array[:, 0]))]
        for i in range(len(spike_array_spikes)):
            numpy.testing.assert_array_equal(
                spike_array_spikes[i], boxed_array[i])
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)

        sim.end()

    def test_recording_1_element(self):
        self.runsafe(self.recording_1_element)

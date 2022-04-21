# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

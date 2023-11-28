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
import pyNN.spiNNaker as p


class TestSpikeSourceArray(BaseTestCase):
    __name__ = "bOB"

    def recording_1_element(self):
        p.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 200  # number of neurons in each population
        p.set_number_of_neurons_per_core(p.IF_curr_exp, n_neurons / 2)

        cell_params_lif = {'cm': 0.25,
                           'i_offset': 0.0,
                           'tau_m': 20.0,
                           'tau_refrac': 2.0,
                           'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0,
                           'v_reset': -70.0,
                           'v_rest': -65.0,
                           'v_thresh': -50.0
                           }

        populations = list()
        projections = list()

        spike_array = {'spike_times': [[0]]}
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif,
                                        label='pop_1'))
        populations.append(p.Population(1, p.SpikeSourceArray, spike_array,
                                        label='inputSpikes_1'))

        projections.append(p.Projection(populations[1], populations[0],
                                        p.AllToAllConnector()))

        populations[1].record("spikes")

        p.run(5000)

        spike_array_spikes = populations[1].spinnaker_get_data("spikes")
        boxed_array = numpy.zeros(shape=(0, 2))
        boxed_array = numpy.append(boxed_array, [[0, 0]], axis=0)
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)

        p.end()

    def test_recording_1_element(self):
        self.runsafe(self.recording_1_element)

    def recording_numerous_elements(self, run_zero):
        p.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 20  # number of neurons in each population
        p.set_number_of_neurons_per_core(p.IF_curr_exp, n_neurons / 2)
        random.seed(12480235)

        cell_params_lif = {'cm': 0.25,
                           'i_offset': 0.0,
                           'tau_m': 20.0,
                           'tau_refrac': 2.0,
                           'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0,
                           'v_reset': -70.0,
                           'v_rest': -65.0,
                           'v_thresh': -50.0
                           }

        populations = list()
        projections = list()

        boxed_array = numpy.zeros(shape=(0, 2))
        spike_array = list()
        for neuron_id in range(0, n_neurons):
            spike_array.append(list())
            for counter in range(0, 20):
                random_time = random.randint(0, 4999)
                boxed_array = numpy.append(
                    boxed_array, [[neuron_id, random_time]], axis=0)
                spike_array[neuron_id].append(random_time)
        spike_array_params = {'spike_times': spike_array}
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif,
                                        label='pop_1'))
        populations.append(p.Population(n_neurons, p.SpikeSourceArray,
                                        spike_array_params,
                                        label='inputSpikes_1'))

        projections.append(p.Projection(populations[1], populations[0],
                                        p.OneToOneConnector()))

        populations[1].record("spikes")

        if run_zero:
            p.run(0)
        p.run(5000)

        spike_array_spikes = populations[1].spinnaker_get_data("spikes")
        boxed_array = boxed_array[numpy.lexsort((boxed_array[:, 1],
                                                 boxed_array[:, 0]))]
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)
        p.end()

    def recording_numerous_elements_no_zero(self):
        self.recording_numerous_elements(False)

    def test_recording_numerous_elements_no_zero(self):
        self.runsafe(self.recording_numerous_elements_no_zero)

    def recording_numerous_elements_with_zero(self):
        self.recording_numerous_elements(True)

    def test_recording_numerous_element_with_zero(self):
        self.runsafe(self.recording_numerous_elements_with_zero)

    def recording_with_empty_lists_first_empty(self):
        p.setup(timestep=1.0)
        p.set_number_of_neurons_per_core(p.SpikeSourceArray, 2)
        spike_times = [[], [1], [], [], [4], [3]]
        input1 = p.Population(
            6, p.SpikeSourceArray(spike_times=spike_times), label="input1")
        input1.record("spikes")
        p.run(50)

        neo = input1.get_data(variables=["spikes"])
        spikes = neo.segments[0].spiketrains

        spikes_test = [list(spikes[i].times.magnitude) for i in range(
            len(spikes))]
        self.assertListEqual(spikes_test, spike_times)

        p.end()

    def test_recording_with_empty_lists_first_empty(self):
        self.runsafe(self.recording_with_empty_lists_first_empty)

    def recording_with_empty_lists_first_not_empty(self):
        p.setup(timestep=1.0)
        p.set_number_of_neurons_per_core(p.SpikeSourceArray, 2)
        spike_times = [[1], [], [], [], [4], [3]]
        input1 = p.Population(
            6, p.SpikeSourceArray(spike_times=spike_times), label="input1")
        input1.record("spikes")
        p.run(50)

        neo = input1.get_data(variables=["spikes"])
        spikes = neo.segments[0].spiketrains

        spikes_test = [list(spikes[i].times.magnitude) for i in range(
            len(spikes))]
        self.assertListEqual(spikes_test, spike_times)

        p.end()

    def test_recording_with_empty_lists_first_not_empty(self):
        self.runsafe(self.recording_with_empty_lists_first_not_empty)

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
import spynnaker8 as p


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
        numpy.testing.assert_array_equal(spikes_test, spike_times)

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
        numpy.testing.assert_array_equal(spikes_test, spike_times)

        p.end()

    def test_recording_with_empty_lists_first_not_empty(self):
        self.runsafe(self.recording_with_empty_lists_first_not_empty)

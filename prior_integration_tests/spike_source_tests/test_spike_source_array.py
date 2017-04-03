import unittest
import spynnaker.pyNN as p
import numpy
import random
import pytest

cell_params_lif = {'cm': 0.25,
                   'i_offset': 0.0,
                   'tau_m': 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E': 5.0,
                   'tau_syn_I': 5.0,
                   'v_reset': -70.0,
                   'v_rest': -65.0,
                   'v_thresh': -50.0}


class TestSpikeSourceArray(unittest.TestCase):
    def setUp(self):
        p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

    def tearDown(self):
        p.end()

    @pytest.mark.timeout(60)
    def test_recording_1_element(self):
        n_neurons = 200  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()
        spike_array = {'spike_times': [[0]]}
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_1'))
        populations.append(p.Population(1, p.SpikeSourceArray, spike_array,
                                        label='inputSpikes_1'))
        projections.append(p.Projection(populations[1], populations[0],
                                        p.AllToAllConnector()))
        populations[1].record()

        p.run(5000)

        spike_array_spikes = populations[1].getSpikes()
        boxed_array = numpy.zeros(shape=(0, 2))
        boxed_array = numpy.append(boxed_array, [[0, 0]], axis=0)
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)

    @pytest.mark.timeout(60)
    def test_recording_numerious_element(self):
        n_neurons = 20  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()
        boxed_array = numpy.zeros(shape=(0, 2))
        spike_array = list()
        for neuron_id in range(0, n_neurons):
            spike_array.append(list())
            for random_time in range(0, 20):
                random_time2 = random.randint(0, 5000)
                boxed_array = numpy.append(
                    boxed_array, [[neuron_id, random_time2]], axis=0)
                spike_array[neuron_id].append(random_time)
        spike_array_params = {'spike_times': spike_array}
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_1'))
        populations.append(p.Population(n_neurons, p.SpikeSourceArray,
                                        spike_array_params,
                                        label='inputSpikes_1'))
        projections.append(p.Projection(populations[1], populations[0],
                                        p.OneToOneConnector()))
        populations[1].record()

        p.run(5000)

        spike_array_spikes = populations[1].getSpikes()
        boxed_array = boxed_array[numpy.lexsort((boxed_array[:, 1],
                                                 boxed_array[:, 0]))]
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)

    @pytest.mark.timeout(60)
    def test_recording_numerious_element_over_limit(self):
        n_neurons = 2000  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", n_neurons / 2)

        populations = list()
        projections = list()
        boxed_array = numpy.zeros(shape=(0, 2))
        spike_array = list()
        for neuron_id in range(0, n_neurons):
            spike_array.append(list())
            for random_time in range(0, 200000):
                random_time2 = random.randint(0, 50000)
                boxed_array = numpy.append(
                    boxed_array, [[neuron_id, random_time2]], axis=0)
                spike_array[neuron_id].append(random_time)
        spike_array_params = {'spike_times': spike_array}
        populations.append(p.Population(n_neurons, p.IF_curr_exp,
                                        cell_params_lif, label='pop_1'))
        populations.append(p.Population(n_neurons, p.SpikeSourceArray,
                                        spike_array_params,
                                        label='inputSpikes_1'))
        projections.append(p.Projection(populations[1], populations[0],
                                        p.OneToOneConnector()))
        populations[1].record()

        p.run(50000)

        spike_array_spikes = populations[1].getSpikes()
        boxed_array = boxed_array[numpy.lexsort((boxed_array[:, 1],
                                                 boxed_array[:, 0]))]
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)


if __name__ == '__main__':
    unittest.main()

import unittest
import spynnaker.pyNN as p
import numpy
import random

class MyTestCase(unittest.TestCase):

    @unittest.skip
    def test_recording_1_element(self):
        p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
        nNeurons = 200  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)


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

        weight_to_spike = 2.0
        delay = 17

        loopConnections = list()
        for i in range(0, nNeurons):
            singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
            loopConnections.append(singleConnection)

        injectionConnection = [(0, 0, weight_to_spike, 1)]
        spikeArray = {'spike_times': [[0]]}
        populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                           label='pop_1'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                           label='inputSpikes_1'))

        projections.append(p.Projection(populations[0], populations[0],
                           p.FromListConnector(loopConnections)))
        projections.append(p.Projection(populations[1], populations[0],
                           p.FromListConnector(injectionConnection)))

        populations[1].record()

        p.run(5000)

        spike_array_spikes = populations[1].getSpikes()
        boxed_array = numpy.ndarray(shape=(0, 2))
        boxed_array = numpy.append(boxed_array, [0, 0])
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)

        p.end()

    def test_recording_numerious_element(self):
        p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
        nNeurons = 20  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_curr_exp", nNeurons / 2)


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

        weight_to_spike = 2.0
        delay = 17

        boxed_array = numpy.zeros(shape=(0, 2))
        spikeArray = list()
        for neuron_id in range(0, nNeurons):
            spikeArray.append(list())
            for random_time in range(0, 20):
                random_time = random.randint(0, 5000)
                boxed_array = numpy.append(boxed_array, [[neuron_id, random_time]], axis=0)
                spikeArray[neuron_id].append(random_time)
        spikeArrayParams = {'spike_times': spikeArray}
        populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                           label='pop_1'))
        populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArrayParams,
                           label='inputSpikes_1'))

        projections.append(p.Projection(populations[1], populations[0],
                           p.OneToOneConnector()))

        populations[1].record()

        p.run(5000)

        spike_array_spikes = populations[1].getSpikes()
        boxed_array = boxed_array[numpy.lexsort((boxed_array[:, 1],
                                                 boxed_array[:, 0]))]
        numpy.testing.assert_array_equal(spike_array_spikes, boxed_array)
        p.end()

if __name__ == '__main__':
    unittest.main()

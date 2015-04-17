"""
Synfirechain-like example
"""

# spynnaker imports
import spynnaker.pyNN as p

# general imports
import os
import pylab
import unittest


def read_spikefile(file_name, n_neurons):
    """
    helper method for reading in spike data
    :param file_name:
    :param n_neurons:
    :return:
    """
    spike_array = [[] for x in range(n_neurons)]
    with open(file_name) as f_spike:
        for line in f_spike:
            cut_index = line.find(';')
            time_stamp = int(line[0:cut_index])
            neuron_list = line[cut_index+1:-1].split(',')
            for neuron in neuron_list:
                neuron_id = int(neuron)
                spike_array[neuron_id].append(time_stamp)
    return spike_array


class TestReadingSpikeArrayDataAndBigSlices(unittest.TestCase):
    """
    tests the printing of print v given a simulation
    """

    def test_script(self):
        """
        test that tests the printing of v from a pre determined recording
        :return:
        """
        p.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
        nNeurons = 128 * 128  # number of neurons in each population
        p.set_number_of_neurons_per_core("IF_cond_exp", nNeurons / 2)

        cell_params_lif = {'cm': 0.25,
                           'i_offset': 0.0,
                           'tau_m': 20.0,
                           'tau_refrac': 2.0,
                           'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0,
                           'v_reset': -70.0,
                           'v_rest': -65.0,
                           'v_thresh': -50.0,
                           'e_rev_E': 0.,
                           'e_rev_I': -80.
                           }

        populations = list()
        projections = list()

        weight_to_spike = 0.035
        delay = 17

        spikes = read_spikefile('test.spikes', nNeurons)
        print spikes
        spikeArray = {'spike_times':  spikes}


        #populations.append(p.Population(nNeurons, p.SpikeSourceArray, spikeArray,
         #                               label='inputSpikes_1'))
        populations.append(p.Population(nNeurons, p.IF_cond_exp, cell_params_lif,
                                        label='pop_1'))
        #projections.append(p.Projection(populations[0], populations[1],
         #                               p.OneToOneConnector(
          #                                  weights= weight_to_spike,
           #                                 delays = delay)))
        #populations[0].record_v()
        #populations[0].record_gsyn()
      #  populations[1].record()

        p.run(10000)

        v = None
        gsyn = None
        spikes = None

        #v = populations[0].get_v(compatible_output=True)
        #gsyn = populations[0].get_gsyn(compatible_output=True)
        spikes = populations[1].getSpikes(compatible_output=True)

        if spikes is not None:
            print spikes
            pylab.figure()
            pylab.plot([i[1] for i in spikes], [i[0] for i in spikes], ".")
            pylab.xlabel('Time/ms')
            pylab.ylabel('spikes')
            pylab.title('spikes')
            pylab.show()
        else:
            print "No spikes received"

        if v is not None:
            ticks = len(v) / nNeurons
            pylab.figure()
            pylab.xlabel('Time/ms')
            pylab.ylabel('v')
            pylab.title('v')
            for pos in range(0, nNeurons, 20):
                v_for_neuron = v[pos * ticks: (pos + 1) * ticks]
                pylab.plot([i[2] for i in v_for_neuron])
            pylab.show()

        if gsyn is not None:
            ticks = len(gsyn) / nNeurons
            pylab.figure()
            pylab.xlabel('Time/ms')
            pylab.ylabel('gsyn')
            pylab.title('gsyn')
            for pos in range(0, nNeurons, 20):
                gsyn_for_neuron = gsyn[pos * ticks: (pos + 1) * ticks]
                pylab.plot([i[2] for i in gsyn_for_neuron])
            pylab.show()

        p.end()

if __name__ == '__main__':
    unittest.main()
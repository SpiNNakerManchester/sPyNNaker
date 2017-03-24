"""
Synfirechain-like example
"""
# !/usr/bin/python
import spynnaker.pyNN as p
import unittest

import spynnaker.plot_utils as plot_utils

def do_run(nNeurons):

    p.setup(timestep=0.1, min_delay = 1.0, max_delay = 7.5)
    p.set_number_of_neurons_per_core("IF_curr_exp", 100)

    input_cell_params = {'cm'        : 0.25, # nF
                         'i_offset'  : 5.0,
                         'tau_m'     : 10.0,
                         'tau_refrac': 2.0,
                         'tau_syn_E' : 0.5,
                         'tau_syn_I' : 0.5,
                         'v_reset'   : -65.0,
                         'v_rest'    : -65.0,
                         'v_thresh'  : -64.4
                         }

    cell_params_lif   = {'cm'        : 0.25, # nF
                         'i_offset'  : 0.0,
                         'tau_m'     : 10.0,
                         'tau_refrac': 2.0,
                         'tau_syn_E' : 0.5,
                         'tau_syn_I' : 0.5,
                         'v_reset'   : -65.0,
                         'v_rest'    : -65.0,
                         'v_thresh'  : -64.4
                         }

    populations = list()
    projections = list()

    weight_to_spike = 0.5
    #delay = 3.1
    injection_delay = 2
    delay = 1

    spikeArray = {'spike_times': [[0, 10, 20, 30]]}
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray, label='pop_0'))
    #populations.append(p.Population(nNeurons, p.IF_curr_exp, input_cell_params, label='pop_0'))
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_1'))
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif, label='pop_2'))

    #projections.append(p.Projection(populations[0], populations[1], p.OneToOneConnector(weights=weight_to_spike, delays=delay)))
    projections.append(p.Projection(populations[0], populations[1], p.AllToAllConnector(weights=weight_to_spike, delays=injection_delay)))
    projections.append(p.Projection(populations[1], populations[2], p.OneToOneConnector(weights=weight_to_spike, delays=delay)))
    #projections.append(p.Projection(populations[1], populations[0], p.FromListConnector([(0, 0, weight_to_spike, injection_delay)])))

    populations[2].record_v()
    populations[2].record()

    p.run(100)

    v = populations[2].get_v(compatible_output=True)
    spikes = populations[2].getSpikes(compatible_output=True)

    p.end()

    return (v, spikes)


class MwhSynfire(unittest.TestCase):
    def test_run(self):
        nNeurons = 3  # number of neurons in each population
        (v, spikes) = do_run(nNeurons)
        # plot_utils.plot_spikes(spikes)
        # plot_utils.heat_plot(v, title="v")
        # print len(spikes)
        self.assertLess(10, len(spikes))
        self.assertGreater(15, len(spikes))


if __name__ == '__main__':
    nNeurons = 3  # number of neurons in each population
    (v, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")

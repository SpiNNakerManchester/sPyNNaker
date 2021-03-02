#!/usr/bin/python

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

"""
Synfirechain-like example
"""
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
import spynnaker8 as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 250)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 5.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 1.5
    delay = 1

    connections = list()
    for i in range(0, nNeurons):
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, delay)]

    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    projections.append(p.Projection(populations[0], populations[0],
                                    p.FromListConnector(connections)))
    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector(injectionConnection)))

    populations[0].record("v")
    populations[0].record("gsyn_exc")
    populations[0].record("spikes")

    p.run(1000)

    ''''
    weights = projections[0].getWeights()
    delays = projections[0].getDelays()
    '''

    neo = populations[0].get_data(["v", "spikes", "gsyn_exc"])

    v = neo_convertor.convert_data(neo, name="v")
    gsyn = neo_convertor.convert_data(neo, name="gsyn_exc")
    spikes = neo_convertor.convert_spikes(neo)

    p.end()

    return (v, gsyn, spikes)


class MwhSynfire(BaseTestCase):
    def test_run(self):
        nNeurons = 100  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        spike_checker.synfire_spike_checker(spikes, nNeurons)
        self.assertEqual(199, len(spikes))


if __name__ == '__main__':
    nNeurons = 100  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

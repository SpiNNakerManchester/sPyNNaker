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
import spynnaker8 as p
from spynnaker.pyNN.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 10.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                       'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -64.4}

    populations = list()
    projections = list()

    weight_to_spike = 2
    injection_delay = 2
    delay = 10

    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    synapse_type = p.StaticSynapse(weight=weight_to_spike, delay=delay)
    connector = p.AllToAllConnector()
    projections.append(p.Projection(populations[0], populations[0], connector,
                                    synapse_type=synapse_type))
    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector([(0, 0, 4,
                                                          injection_delay)])))

    populations[0].record("v")
    populations[0].record("gsyn_exc")
    populations[0].record("spikes")

    p.run(90)

    neo = populations[0].get_data(["v", "spikes", "gsyn_exc"])

    v = neo_convertor.convert_data(neo, name="v")
    gsyn = neo_convertor.convert_data(neo, name="gsyn_exc")
    spikes = neo_convertor.convert_spikes(neo)

    p.end()

    return (v, gsyn, spikes)


class ParamsSetAsList(BaseTestCase):

    def test_run(self):
        nNeurons = 2  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        self.assertEqual(17, len(spikes))


if __name__ == '__main__':
    nNeurons = 2  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

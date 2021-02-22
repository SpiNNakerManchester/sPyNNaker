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
from unittest import SkipTest
from spinnman.exceptions import SpinnmanTimeoutException
import spynnaker.plot_utils as plot_utils
import spynnaker8 as p
from spynnaker.pyNN.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase


def do_run(nNeurons, neurons_per_core):

    p.setup(timestep=1.0, min_delay=1.0, max_delay=32.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, neurons_per_core)

    nPopulations = 62
    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 5.0, 'tau_syn_I': 5.0,
                       'v_reset': -70.0, 'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    weight_to_spike = 1.5
    delay = 5

    for i in range(0, nPopulations):
        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif,
                                        label='pop_' + str(i)))
        # print("++++++++++++++++")
        # print("Added population %s" % (i))
        # print("o-o-o-o-o-o-o-o-")
    synapse_type = p.StaticSynapse(weight=weight_to_spike, delay=delay)
    for i in range(0, nPopulations):
        projections.append(p.Projection(populations[i],
                                        populations[(i + 1) % nPopulations],
                                        p.OneToOneConnector(),
                                        synapse_type=synapse_type,
                                        label="Projection from pop {} to pop "
                                              "{}".format(i, (i + 1) %
                                                          nPopulations)))
        # print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # print("Added projection from population %s to population %s" \
        #      % (i, (i + 1) % nPopulations))
        # print("----------------------------------------------------")

    # from pprint import pprint as pp
    # pp(projections)
    spikeArray = {'spike_times': [[0]]}
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))
    projections.append(p.Projection(populations[-1], populations[0],
                                    p.AllToAllConnector(),
                                    synapse_type=synapse_type))

    for i in range(0, nPopulations):
        populations[i].record("v")
        populations[i].record("gsyn_exc")
        populations[i].record("spikes")

    p.run(1500)

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


class MwhPopulationSynfire(BaseTestCase):

    def test_run_heavy(self):
        self.assert_not_spin_three()
        try:
            nNeurons = 200  # number of neurons in each population
            neurons_per_core = 256
            (v, gsyn, spikes) = do_run(nNeurons, neurons_per_core)
            self.assertEqual(600, len(spikes))
        except SpinnmanTimeoutException as ex:
            raise SkipTest() from ex
        self.assertEqual(600, len(spikes))

    def test_run_light(self):
        self.assert_not_spin_three()
        nNeurons = 200  # number of neurons in each population
        neurons_per_core = 50
        (v, gsyn, spikes) = do_run(nNeurons, neurons_per_core)
        self.assertEqual(600, len(spikes))


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    neurons_per_core = 256
    (v, gsyn, spikes) = do_run(nNeurons, neurons_per_core)
    plot_utils.plot_spikes(spikes)
    plot_utils.line_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

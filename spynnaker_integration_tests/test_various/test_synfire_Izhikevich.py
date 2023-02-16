#!/usr/bin/python

# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Synfirechain-like example
"""
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
import pyNN.spiNNaker as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0)
    p.set_number_of_neurons_per_core(p.Izhikevich, 100)

    cell_params_izk = {
        'a': 0.02,
        'b': 0.2,
        'c': -65,
        'd': 8,
        'v': -75,
        'u': 0,
        'tau_syn_E': 2,
        'tau_syn_I': 2,
        'i_offset': 0
        }

    populations = list()
    projections = list()

    weight_to_spike = 40
    delay = 1

    connections = list()
    for i in range(0, nNeurons):
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, delay)]
    spikeArray = {'spike_times': [[50]]}
    populations.append(p.Population(nNeurons, p.Izhikevich, cell_params_izk,
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

    p.run(500)

    neo = populations[0].get_data(["v", "spikes", "gsyn_exc"])

    v = neo_convertor.convert_data(neo, name="v")
    gsyn = neo_convertor.convert_data(neo, name="gsyn_exc")
    spikes = neo_convertor.convert_spikes(neo)

    p.end()

    return (v, gsyn, spikes)


class SynfireIzhikevich(BaseTestCase):

    def check_run(self):
        nNeurons = 200  # number of neurons in each population
        (v, gsyn, spikes) = do_run(nNeurons)
        spike_checker.synfire_spike_checker(spikes, nNeurons)
        self.assertEqual(215, len(spikes))

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    (v, gsyn, spikes) = do_run(nNeurons)
    print(len(spikes))
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v, title="v")
    plot_utils.heat_plot(gsyn, title="gsyn")

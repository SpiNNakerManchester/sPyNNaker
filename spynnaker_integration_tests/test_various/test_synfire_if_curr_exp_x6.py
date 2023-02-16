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
Synfirechain-like example with 6 chains
"""
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run(nNeurons):
    p.setup(timestep=1.0, min_delay=1.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)

    cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 10.0,
                       'tau_refrac': 2.0, 'tau_syn_E': 0.5, 'tau_syn_I': 0.5,
                       'v_reset': -65.0, 'v_rest': -65.0, 'v_thresh': -64.4}

    populations = list()
    projections = list()

    weight_to_spike = 2
    delay = 1

    connections = list()
    for i in range(0, nNeurons):
        singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike, delay)
        connections.append(singleConnection)

    injectionConnection = [(0, 0, weight_to_spike, delay)]
    spikeArray = {'spike_times': [[0]]}
    for x in range(6):
        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray))

    for x in range(0, 12, 2):
        projections.append(p.Projection(populations[x], populations[x],
                                        p.FromListConnector(connections)))
        connector = p.FromListConnector(injectionConnection)
        projections.append(p.Projection(populations[x+1], populations[x],
                                        connector))
        populations[x].record("spikes")

    p.run(1000)

    spikes = []
    for x in range(0, 12, 2):
        spikes.append(populations[x].spinnaker_get_data("spikes"))

    p.end()

    return spikes


class SynfireIfCurrx6(BaseTestCase):

    def check_run(self):
        nNeurons = 200  # number of neurons in each population
        spikes = do_run(nNeurons)
        for x in range(0, 12, 2):
            self.assertEqual(999, len(spikes[x // 2]))

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    nNeurons = 200  # number of neurons in each population
    spikes = do_run(nNeurons)
    for x in range(0, 12, 2):
        print(x, len(spikes[x // 2]))

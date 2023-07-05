# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pyNN.random import RandomDistribution
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run(nNeurons):

    p.setup(timestep=1.0, min_delay=1.0)

    p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)

    cm = list()
    i_off = list()
    tau_m = list()
    tau_re = list()
    tau_syn_e = list()
    tau_syn_i = list()
    v_reset = list()
    v_rest = list()
    v_thresh = list()

    for _ in range(0, nNeurons):
        cm.append(0.25)
        i_off.append(0.0)
        tau_m.append(10.0)
        tau_re.append(2.0)
        tau_syn_e.append(0.5)
        tau_syn_i.append(0.5)
        v_reset.append(-65.0)
        v_rest.append(-65.0)
        v_thresh.append(-64.4)

    gbar_na_distr = RandomDistribution('normal', (20.0, 2.0))

    cell_params_lif = {'cm': cm, 'i_offset': i_off, 'tau_m': tau_m,
                       'tau_refrac': tau_re, 'tau_syn_E': tau_syn_e,
                       'tau_syn_I': tau_syn_i, 'v_reset': v_reset,
                       'v_rest': v_rest, 'v_thresh': v_thresh}

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
    populations.append(p.Population(nNeurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1', seed=85524))
    populations.append(p.Population(1, p.SpikeSourceArray, spikeArray,
                                    label='inputSpikes_1'))

    populations[0].set(cm=0.25)
    populations[0].set(cm=cm)
    populations[0].set(tau_m=tau_m, v_thresh=v_thresh)
    populations[0].set(i_offset=gbar_na_distr)
    populations[0].set(i_offset=i_off)

    projections.append(p.Projection(populations[0], populations[0],
                                    p.FromListConnector(connections)))
    projections.append(p.Projection(populations[1], populations[0],
                                    p.FromListConnector(injectionConnection)))

    populations[0].record("v")
    populations[0].record("gsyn_exc")
    populations[0].record("spikes")

    p.run(100)

    neo = populations[0].get_data(["v", "spikes", "gsyn_exc"])

    p.end()

    return neo


class ParamsSetAsList(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_run(self):
        do_run(225)  # number of neurons in each population


if __name__ == '__main__':
    do_run(225)  # number of neurons in each population

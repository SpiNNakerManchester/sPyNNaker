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

from pyNN.random import RandomDistribution, NumpyRNG
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

    for atom in range(0, nNeurons):
        cm.append(0.25)
        i_off.append(0.0)
        tau_m.append(10.0)
        tau_re.append(2.0)
        tau_syn_e.append(0.5)
        tau_syn_i.append(0.5)
        v_reset.append(-65.0)
        v_rest.append(-65.0)
        v_thresh.append(-64.4)

    gbar_na_distr = RandomDistribution('normal', (20.0, 2.0),
                                       rng=NumpyRNG(seed=85524))

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
                                    label='pop_1'))
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
        nNeurons = 225  # number of neurons in each population
        do_run(nNeurons)


if __name__ == '__main__':
    nNeurons = 225  # number of neurons in each population
    do_run(nNeurons)

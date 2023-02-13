# Copyright (c) 2017-2023 The University of Manchester
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

import numpy
import spynnaker.plot_utils as plot_utils
import pyNN.spiNNaker as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(n_neurons, n_cores, i_offset2, i_offset3):
    p.setup(timestep=1.0, min_delay=1.0)
    p.set_number_of_neurons_per_core(p.Izhikevich, n_neurons / n_cores)
    cell_params_izk = {'a': 0.02,
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
    populations.append(p.Population(n_neurons, p.Izhikevich, cell_params_izk,
                                    label='pop_1'))
    populations[0].record("spikes")
    p.run(1000)
    populations[0].set(i_offset=i_offset2)
    p.run(1000)
    populations[0].set(i_offset=i_offset3)
    p.run(1000)
    neo = populations[0].get_data()

    p.end()

    return neo


class TestSetTOffset(BaseTestCase):
    expected = [2011., 2148., 2288., 2427., 2565., 2703., 2844., 2982.]

    def one_core(self):
        n_neurons = 32
        n_cores = 1
        neo = do_run(n_neurons, n_cores, 2, 4)
        spiketrains = neo.segments[0].spiketrains
        for spiketrain in spiketrains:
            assert numpy.array_equal(spiketrain.magnitude, self.expected)

    def test_one_core(self):
        self.runsafe(self.one_core)


if __name__ == '__main__':
    n_neurons = 40
    n_cores = 3
    neo = do_run(n_neurons, n_cores, 2, 4)
    spikes = neo_convertor.convert_spikes(neo)

    print(spikes)
    plot_utils.plot_spikes(spikes)

    times = set(spikes[:, 1])
    print(n_neurons * len(times), len(spikes))

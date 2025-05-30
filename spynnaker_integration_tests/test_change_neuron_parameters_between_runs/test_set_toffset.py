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

from neo.core import Block
import numpy
import pyNN.spiNNaker as p
from spynnaker.pyNN.utilities import neo_convertor
from spinnaker_testbase import BaseTestCase


def do_run(n_neurons: int, n_cores: int, i_offset2: int,
           i_offset3: int) -> Block:
    p.setup(timestep=1.0, min_delay=1.0)
    p.set_number_of_neurons_per_core(p.IF_curr_exp, n_neurons / n_cores)

    cell_params_lif = {'cm': 0.25,
                       'i_offset': 0.0,
                       'tau_m': 20.0,
                       'tau_refrac': 2.0,
                       'tau_syn_E': 5.0,
                       'tau_syn_I': 5.0,
                       'v_reset': -70.0,
                       'v_rest': -65.0,
                       'v_thresh': -50.0
                       }

    populations = list()

    populations.append(p.Population(n_neurons, p.IF_curr_exp, cell_params_lif,
                                    label='pop_1'))

    populations[0].record("spikes")

    p.run(100)

    populations[0].set(i_offset=i_offset2)

    p.run(100)

    populations[0].set(i_offset=i_offset3)

    p.run(100)

    neo = populations[0].get_data()

    p.end()

    return neo


class TestSetTOffset(BaseTestCase):
    expected = [104., 112., 120., 128., 136., 144., 152., 160., 168., 176.,
                184., 192., 200., 205., 210., 215., 220., 225., 230., 235.,
                240., 245., 250., 255., 260., 265., 270., 275., 280., 285.,
                290., 295.]

    def one_core(self) -> None:
        n_neurons = 6
        n_cores = 1
        neo = do_run(n_neurons, n_cores, 1, 2)
        spiketrains = neo.segments[0].spiketrains
        for spiketrain in spiketrains:
            assert numpy.array_equal(spiketrain.magnitude, self.expected)

    def test_one_core(self) -> None:
        self.runsafe(self.one_core)

    def three_cores(self) -> None:
        n_neurons = 6
        n_cores = 3
        neo = do_run(n_neurons, n_cores, 1, 2)
        spiketrains = neo.segments[0].spiketrains
        for spiketrain in spiketrains:
            assert numpy.array_equal(spiketrain.magnitude, self.expected)

    def test_three_cores(self) -> None:
        self.runsafe(self.three_cores)


if __name__ == '__main__':
    n_neurons = 40
    n_cores = 3
    neo = do_run(n_neurons, n_cores, 1, 2)
    spikes = neo_convertor.convert_spikes(neo)
    v = neo_convertor.convert_data(neo, "v")
    gsyn = neo_convertor.convert_data(neo, "gsyn_exc")

    print(spikes)
    print(v)
    print(gsyn)

    times = set(spikes[:, 1])
    print(n_neurons * len(times), len(spikes))

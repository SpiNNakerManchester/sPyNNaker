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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.utilities import neo_convertor


def do_run(m_size):

    p.setup(timestep=1.0)

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

    def create_grid(n, label, dx=1.0, dy=1.0):
        grid_structure = p.Grid2D(dx=dx, dy=dy, x0=0.0, y0=0.0)
        return p.Population(n*n, p.IF_curr_exp(**cell_params_lif),
                            structure=grid_structure, label=label)

    # Parameters
    n = 5
    weight_to_spike = 2.0
    delay = 2
    runtime = 35

    # Network population
    small_world = create_grid(n, 'small_world')
    small_world.set_max_atoms_per_core(m_size)

    # SpikeInjector
    injectionConnection = [(0, 0)]
    spikeArray = {'spike_times': [[0]]}
    inj_pop = p.Population(1, p.SpikeSourceArray(**spikeArray),
                           label='inputSpikes_1')

    # Injector projection
    p.Projection(inj_pop, small_world,
                 p.FromListConnector(injectionConnection),
                 p.StaticSynapse(weight=weight_to_spike, delay=delay))

    # Connectors
    degree = 2.0
    rewiring = 0.0

    small_world_connector = p.SmallWorldConnector(degree, rewiring)

    # Projection for small world grid
    sw_pro = p.Projection(small_world, small_world, small_world_connector,
                          p.StaticSynapse(weight=2.0, delay=5))

    small_world.record(['spikes'])

    p.run(runtime)

    spikes = small_world.get_data('spikes').segments[0].spiketrains
    weights = sw_pro.get('weight', 'list')
    p.end()

    return spikes, weights


class SmallWorldConnectorFixedTest(BaseTestCase):
    S_DICT = {0: {0, 1, 5, 6},
               1: {0, 1, 2, 5, 6, 7},
               2: {1, 2, 3, 6, 7, 8},
               3: {2, 3, 4, 7, 8, 9},
               4: {8, 9, 3, 4},
               5: {0, 1, 5, 6, 10, 11},
               6: {0, 1, 2, 5, 6, 7, 10, 11, 12},
               7: {1, 2, 3, 6, 7, 8, 11, 12, 13},
               8: {2, 3, 4, 7, 8, 9, 12, 13, 14},
               9: {3, 4, 8, 9, 13, 14},
               10: {5, 6, 10, 11, 15, 16},
               11: {5, 6, 7, 10, 11, 12, 15, 16, 17},
               12: {6, 7, 8, 11, 12, 13, 16, 17, 18},
               13: {7, 8, 9, 12, 13, 14, 17, 18, 19},
               14: {8, 9, 13, 14, 18, 19},
               15: {10, 11, 15, 16, 20, 21},
               16: {10, 11, 12, 15, 16, 17, 20, 21, 22},
               17: {11, 12, 13, 16, 17, 18, 21, 22, 23},
               18: {12, 13, 14, 17, 18, 19, 22, 23, 24},
               19: {13, 14, 18, 19, 23, 24},
               20: {16, 20, 21, 15},
               21: {15, 16, 17, 20, 21, 22},
               22: {16, 17, 18, 21, 22, 23},
               23: {17, 18, 19, 22, 23, 24},
               24: {24, 18, 19, 23}}

    FIRSTS = [4, 11, 17, 23, 29,
              11, 11, 17, 23, 28,
              17, 17, 18, 23, 29,
              23, 23, 23, 25, 30,
              29, 28, 29, 30, 32]

    def directly_connected(self, weights):
        from collections import defaultdict
        singles = defaultdict(set)
        for (s, d, _) in weights:
            singles[s].add(d)
            singles[d].add(s)
        return singles

    def run_1_core(self):
        spikes, weights = do_run([5,5])
        # Not sure checking spike len is telling us much
        for spike_train, first in zip(spikes, self.FIRSTS):
            self.assertEqual(first, spike_train[0].magnitude)

        single_connected = self.directly_connected(weights)
        self.assertDictEqual(self.S_DICT, single_connected)

    def run_many_core(self):
        spikes, weights = do_run([2,2])
        # Not sure checking spike len is telling us much
        for spike_train, first in zip(spikes, self.FIRSTS):
            self.assertAlmostEqual(first, spike_train[0].magnitude, delta=1)

        single_connected = self.directly_connected(weights)
        self.assertDictEqual(self.S_DICT, single_connected)

    def test_1_core(self):
        self.runsafe(self.run_1_core)

    def test_many_core(self):
        self.runsafe(self.run_many_core)

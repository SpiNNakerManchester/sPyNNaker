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


def do_run(m_size, n_atoms_side):

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
    weight_to_spike = 2.0
    delay = 2
    runtime = 35

    # Network population
    small_world = create_grid(n_atoms_side, 'small_world')
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
    degree = 3.0
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
    S_DICT = {0: {0, 1, 2, 6, 7, 8, 12, 13, 14},
              1: {0, 1, 2, 3, 6, 7, 8, 9, 12, 13, 14, 15},
              2: {0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16},
              3: {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17},
              4: {2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 16, 17},
              5: {3, 4, 5, 9, 10, 11, 15, 16, 17},
              6: {0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20},
              7: {0, 1, 2, 3, 6, 7, 8, 9, 12, 13, 14, 15, 18, 19, 20, 21},
              8: {0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19,
                  20, 21, 22},
              9: {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20,
                  21, 22, 23},
              10: {2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 16, 17, 20, 21, 22, 23},
              11: {3, 4, 5, 9, 10, 11, 15, 16, 17, 21, 22, 23},
              12: {0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20, 24, 25, 26},
              13: {0, 1, 2, 3, 6, 7, 8, 9, 12, 13, 14, 15, 18, 19, 20, 21, 24,
                   25, 26, 27},
              14: {0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19,
                   20, 21, 22, 24, 25, 26, 27, 28},
              15: {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20,
                   21, 22, 23, 25, 26, 27, 28, 29},
              16: {2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 16, 17, 20, 21, 22, 23,
                   26, 27, 28, 29},
              17: {3, 4, 5, 9, 10, 11, 15, 16, 17, 21, 22, 23, 27, 28, 29},
              18: {32, 6, 7, 8, 12, 13, 14, 18, 19, 20, 24, 25, 26, 30, 31},
              19: {6, 7, 8, 9, 12, 13, 14, 15, 18, 19, 20, 21, 24, 25, 26, 27,
                   30, 31, 32, 33},
              20: {6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 24,
                   25, 26, 27, 28, 30, 31, 32, 33, 34},
              21: {7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 25,
                   26, 27, 28, 29, 31, 32, 33, 34, 35},
              22: {8, 9, 10, 11, 14, 15, 16, 17, 20, 21, 22, 23, 26, 27, 28,
                   29, 32, 33, 34, 35},
              23: {33, 34, 35, 9, 10, 11, 15, 16, 17, 21, 22, 23, 27, 28, 29},
              24: {32, 12, 13, 14, 18, 19, 20, 24, 25, 26, 30, 31},
              25: {32, 33, 12, 13, 14, 15, 18, 19, 20, 21, 24, 25, 26, 27, 30,
                   31},
              26: {12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28,
                   30, 31, 32, 33, 34},
              27: {13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29,
                   31, 32, 33, 34, 35},
              28: {32, 33, 34, 35, 14, 15, 16, 17, 20, 21, 22, 23, 26, 27, 28,
                   29},
              29: {33, 34, 35, 15, 16, 17, 21, 22, 23, 27, 28, 29},
              30: {32, 18, 19, 20, 24, 25, 26, 30, 31},
              31: {32, 33, 18, 19, 20, 21, 24, 25, 26, 27, 30, 31},
              32: {32, 33, 34, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 30, 31},
              33: {32, 33, 34, 35, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 31},
              34: {32, 33, 34, 35, 20, 21, 22, 23, 26, 27, 28, 29},
              35: {33, 34, 35, 21, 22, 23, 27, 28, 29}}

    FIRSTS = [4, 11, 11, 16, 16, 21,
              11, 11, 11, 16, 16, 21,
              11, 11, 11, 16, 16, 21,
              16, 16, 16, 16, 17, 21,
              16, 16, 16, 17, 18, 21,
              21, 21, 21, 21, 21, 22]

    def directly_connected(self, weights):
        from collections import defaultdict
        singles = defaultdict(set)
        for (s, d, _) in weights:
            singles[s].add(d)
            singles[d].add(s)
        return singles

    def run_1_core(self):
        spikes, weights = do_run([6, 6], 6)

        single_connected = self.directly_connected(weights)
        for spike_train in spikes:
            print(spike_train[0].magnitude)
        print(single_connected)

        # Not sure checking spike len is telling us much
        for spike_train, first in zip(spikes, self.FIRSTS):
            self.assertEqual(first, spike_train[0].magnitude)

        self.assertDictEqual(self.S_DICT, single_connected)

    def run_many_core_2_2(self):
        spikes, weights = do_run([2, 2], 6)

        single_connected = self.directly_connected(weights)
        print(single_connected)
        self.assertDictEqual(self.S_DICT, single_connected)

        # Not sure checking spike len is telling us much
        for spike_train, first in zip(spikes, self.FIRSTS):
            self.assertAlmostEqual(first, spike_train[0].magnitude, delta=1)

    def run_many_core_3_3(self):
        spikes, weights = do_run([3, 3], 6)
        # Not sure checking spike len is telling us much
        for spike_train, first in zip(spikes, self.FIRSTS):
            self.assertAlmostEqual(first, spike_train[0].magnitude, delta=1)

        single_connected = self.directly_connected(weights)
        self.assertDictEqual(self.S_DICT, single_connected)

    def test_1_core(self):
        self.runsafe(self.run_1_core)

    def test_many_core_2_2(self):
        self.runsafe(self.run_many_core_2_2)

    def test_many_core_3_3(self):
        self.runsafe(self.run_many_core_3_3)

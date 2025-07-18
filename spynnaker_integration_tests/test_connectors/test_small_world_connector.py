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

from collections import defaultdict
from typing import Dict, Set, Tuple

import matplotlib.pyplot as plt
from neo import Block
from pyNN.random import NumpyRNG
import pyNN.spiNNaker as p
from pyNN.utility.plotting import Figure, Panel

from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.models.neuron import ConnectionHolder
from spynnaker.pyNN.models.populations import Population
from spynnaker.pyNN.utilities import neo_convertor


def create_grid(n: int, label: str, dx: float = 1.0,
                dy: float = 1.0) -> Population:
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
    grid_structure = p.Grid2D(dx=dx, dy=dy, x0=0.0, y0=0.0)
    return p.Population(n * n, p.IF_curr_exp(**cell_params_lif),
                        structure=grid_structure, label=label)


def do_run(plot: bool) -> Tuple[Block, Block, ConnectionHolder]:

    p.setup(timestep=1.0)

    # Parameters
    n = 5
    weight_to_spike = 2.0
    delay = 2
    runtime = 1000

    # Network population
    small_world = create_grid(n, 'small_world')
    small_world.set_max_atoms_per_core((n, n))

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
    rewiring = 0.4
    rng = NumpyRNG(seed=1)

    small_world_connector = p.SmallWorldConnector(degree, rewiring, rng=rng)

    # Projection for small world grid
    sw_pro = p.Projection(small_world, small_world, small_world_connector,
                          p.StaticSynapse(weight=2.0, delay=5))

    small_world.record(['v', 'spikes'])

    p.run(runtime)

    v = small_world.get_data('v')
    spikes = small_world.get_data('spikes')
    weights = sw_pro.get('weight', 'list')
    if plot:
        Figure(
            # raster plot of the presynaptic neuron spike times
            Panel(spikes.segments[0].spiketrains,
                  yticks=True, markersize=0.2, xlim=(0, runtime), xticks=True),
            # membrane potential of the postsynaptic neuron
            Panel(v.segments[0].filter(name='v')[0],
                  ylabel="Membrane potential (mV)",
                  data_labels=[small_world.label], yticks=True,
                  xlim=(0, runtime), xticks=True),
            title="Simple small world connector",
            annotations="Simulated with {}".format(p.name())
        )
        plt.show()

    p.end()

    return v, spikes, weights


class SmallWorldConnectorTest(BaseTestCase):
    S_COUNTS = [(0, 4), (1, 6), (2, 6), (3, 6), (4, 4),
                (5, 6), (6, 9), (7, 9), (8, 9), (9, 6),
                (10, 6), (11, 9), (12, 9), (13, 9), (14, 6),
                (15, 6), (16, 9), (17, 9), (18, 9), (19, 6),
                (20, 4), (21, 6), (22, 6), (23, 6), (24, 4)]

    def directly_connected(
            self, weights: ConnectionHolder) -> Dict[int, Set[int]]:
        singles: Dict[int, Set[int]] = defaultdict(set)
        for (s, d, _) in weights:
            singles[s].add(d)
            singles[d].add(s)
        return singles

    def next_connected(self, previous: Dict[int, Set[int]],
                       single: Dict[int, Set[int]]) -> Dict[int, Set[int]]:
        current: Dict[int, Set[int]] = dict()
        for i in range(25):
            current[i] = set(previous[i])
            for j in previous[i]:
                current[i].update(single[j])
        return current

    def check_weights(self, weights: ConnectionHolder) -> None:
        s_list = [s for (s, _, _) in weights]
        s_counts = [(i, s_list.count(i)) for i in range(25)]
        self.assertEqual(self.S_COUNTS, s_counts)
        single_connected = self.directly_connected(weights)
        two_step_connected = self.next_connected(
            single_connected, single_connected)
        three_step_connected = self.next_connected(
            two_step_connected, single_connected)

        for i in range(25):
            self.assertEqual(25, len(three_step_connected[i]))

    def a_run(self) -> None:
        v, spikes, weights = do_run(plot=False)
        # any checks go here
        v_test = neo_convertor.convert_data(v, name='v')
        spikes_test = neo_convertor.convert_data(spikes, name='spikes')
        self.assertEqual(25000, len(v_test))
        # Not sure checking spike len is telling us much
        self.assertLess(7750, len(spikes_test))
        self.assertGreater(8250, len(spikes_test))
        self.check_weights(weights)

    def test_a_run(self) -> None:
        self.runsafe(self.a_run)


if __name__ == '__main__':
    _v, _spikes, _weights = do_run(plot=True)
    print(len(neo_convertor.convert_data(_v, name='v')))
    print(len(neo_convertor.convert_data(_spikes, name='spikes')))
    print(len(_weights))

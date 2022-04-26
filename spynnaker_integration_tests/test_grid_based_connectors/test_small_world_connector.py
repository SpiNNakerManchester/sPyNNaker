# Copyright (c) 2017-2022 The University of Manchester
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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from pyNN.utility.plotting import Figure, Panel
from pyNN.random import NumpyRNG
import matplotlib.pyplot as plt
from spynnaker.pyNN.utilities import neo_convertor


def do_run(plot):

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
    runtime = 1000
    p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)

    # Network population
    small_world = create_grid(n, 'small_world')

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
        # pylint: disable=no-member
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

    def directly_connected(self, weights):
        from collections import defaultdict
        singles = defaultdict(set)
        for (s, d, _) in weights:
            singles[s].add(d)
            singles[d].add(s)
        return singles

    def next_connected(self, previous, single):
        current = dict()
        for i in range(25):
            current[i] = set(previous[i])
            for j in previous[i]:
                current[i].update(single[j])
        return current

    def check_weights(self, weights):
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

    def a_run(self):
        v, spikes, weights = do_run(plot=False)
        # any checks go here
        v_test = neo_convertor.convert_data(v, name='v')
        spikes_test = neo_convertor.convert_data(spikes, name='spikes')
        self.assertEqual(25000, len(v_test))
        # Not sure checking spike len is telling us much
        self.assertLess(7750, len(spikes_test))
        self.assertGreater(8250, len(spikes_test))
        self.check_weights(weights)

    def test_a_run(self):
        self.runsafe(self.a_run)


if __name__ == '__main__':
    _v, _spikes, _weights = do_run(plot=True)
    print(len(neo_convertor.convert_data(_v, name='v')))
    print(len(neo_convertor.convert_data(_spikes, name='spikes')))
    print(len(_weights))

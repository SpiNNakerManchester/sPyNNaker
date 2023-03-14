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
import math
from spinnaker_testbase import BaseTestCase
from pyNN.utility.plotting import Figure, Panel
from pyNN.random import NumpyRNG
import matplotlib.pyplot as plt


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
                       'v_thresh': -40.0
                       }

    def create_grid(n, label, dx=1.0, dy=1.0):
        grid_structure = p.Grid2D(dx=dx, dy=dy, x0=0.0, y0=0.0)
        return p.Population(n*n, p.IF_curr_exp(**cell_params_lif),
                            structure=grid_structure, label=label)

    n = 4
    weight_to_spike = 5.0
    delay = 5
    runtime = 200

    # Network
    grid = create_grid(n, 'grid')

    # SpikeInjector
    injectionConnection = [(0, 0)]
    spikeArray = {'spike_times': [[0]]}
    inj_pop = p.Population(1, p.SpikeSourceArray(**spikeArray),
                           label='inputSpikes_1')

    p.Projection(inj_pop, grid, p.FromListConnector(injectionConnection),
                 p.StaticSynapse(weight=weight_to_spike, delay=delay))

    # Connectors
    exc_connector = p.AllToAllConnector()
    inh_connector = p.FixedProbabilityConnector(0.5, rng=NumpyRNG(seed=10101))

    # Wire grid
    exc_proj = p.Projection(grid, grid, exc_connector,
                            p.StaticSynapse(
                                weight="1.0 + (2.0*exp(-d))", delay=5))
    inh_proj = p.Projection(grid, grid, inh_connector,
                            p.StaticSynapse(
                                weight=1.5, delay="2 + 2.0*d"))

    grid.record(['v', 'spikes'])

    p.run(runtime)

    v = grid.get_data('v')
    spikes = grid.get_data('spikes')

    exc_weights_delays = exc_proj.get(['weight', 'delay'], 'list')
    inh_weights_delays = inh_proj.get(['weight', 'delay'], 'list')

    if plot:
        Figure(
            # raster plot of the presynaptic neurons' spike times
            Panel(spikes.segments[0].spiketrains,
                  yticks=True, markersize=0.2, xlim=(0, runtime), xticks=True),
            # membrane potential of the postsynaptic neurons
            Panel(v.segments[0].filter(name='v')[0],
                  ylabel="Membrane potential (mV)",
                  data_labels=[grid.label], yticks=True, xlim=(0, runtime),
                  xticks=True),
            title="Simple 2D grid distance-dependent weights and delays",
            annotations="Simulated with {}".format(p.name())
        )
        plt.show()

    p.end()

    return exc_weights_delays, inh_weights_delays


class DistanceDependentWeightsAndDelaysTest(BaseTestCase):
    POSITIONS = [(i, j) for i in range(4) for j in range(4)]

    def check_exc_weights(self, exc_weights_delays):
        for conn in exc_weights_delays:
            # delays are constant
            self.assertEqual(5, conn[3])
            source_pos = self.POSITIONS[conn[0]]
            target_pos = self.POSITIONS[conn[1]]
            dist = math.sqrt((source_pos[0]-target_pos[0])**2 +
                             (source_pos[1]-target_pos[1])**2)
            weight = 1.0 + (2.0 * math.exp(-dist))
            # The weight from such an equation cannot be represented exactly
            # on SpiNNaker but in this case should be within 3 dp
            self.assertAlmostEqual(weight, conn[2], places=3)

    def check_inh_weights(self, inh_weights_delays):
        for conn in inh_weights_delays:
            # weights are constant
            self.assertEqual(1.5, conn[2])
            source_pos = self.POSITIONS[conn[0]]
            target_pos = self.POSITIONS[conn[1]]
            dist = math.sqrt((source_pos[0]-target_pos[0])**2 +
                             (source_pos[1]-target_pos[1])**2)
            # For ts=1.0 on SpiNNaker delays are rounded to nearest integer
            delay = round(2.0 + (2.0 * dist))
            self.assertEqual(delay, conn[3])

    def a_run(self):
        exc_weights_delays, inh_weights_delays = do_run(plot=False)
        # any checks go here
        self.check_exc_weights(exc_weights_delays)
        self.check_inh_weights(inh_weights_delays)

    def test_a_run(self):
        self.runsafe(self.a_run)


if __name__ == '__main__':
    exc_weights_delays, inh_weights_delays = do_run(plot=True)
    print(len(exc_weights_delays), len(inh_weights_delays))

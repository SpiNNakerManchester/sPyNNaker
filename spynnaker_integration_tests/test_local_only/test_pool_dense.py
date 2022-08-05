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

import numpy
import pyNN.spiNNaker as sim
from pyNN.space import Grid2D
from spinnaker_testbase import BaseTestCase


def do_run():
    numpy.random.seed(13)

    shape = numpy.array([5, 5])
    n_input = numpy.prod(shape)

    vline = [[20. + idx // shape[1]]
             if (idx % shape[1]) == (shape[1] // 2) else []
             for idx in range(n_input)]

    vline0 = [[10. + idx // shape[1]]
              if (idx % shape[1]) == (shape[1] // 2) else []
              for idx in range(n_input)]

    run_time = 60.

    sim.setup(timestep=1.)
    sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, (3, 3))
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 16)

    src = sim.Population(n_input, sim.SpikeSourceArray,
                         {'spike_times': vline},
                         label='input spikes 0',
                         structure=Grid2D(shape[0] / shape[1]))

    src1 = sim.Population(n_input, sim.SpikeSourceArray,
                          {'spike_times': vline0},
                          label='input spikes 1',
                          structure=Grid2D(shape[0] / shape[1]))

    pooling = numpy.array([2, 2])
    post_pool_shape = sim.PoolDenseConnector.get_post_pool_shape(
        shape, pooling)
    n_out = 23
    k_shape = numpy.asarray(
        (int(numpy.prod(post_pool_shape)), n_out), dtype='int')

    ws = numpy.arange(int(numpy.prod(k_shape))).reshape(k_shape) * 0.01
    print(ws.shape)
    print(len(ws))
    print(ws)

    conn = sim.PoolDenseConnector(ws, pooling)
    conn1 = sim.PoolDenseConnector(ws - 1.0, pooling)

    post_cfg = {
        'v_thresh': 5.,
        'v_reset': 0.,
        'v': 0.,
        'v_rest': 0.,
        'tau_syn_E': 1.0,
        'tau_syn_I': 1.0,
        'tau_m': 1.0
    }

    dst = sim.Population(n_out, sim.IF_curr_exp, post_cfg)
    dst.record(['v', 'spikes'])

    sim.Projection(src, dst, conn, sim.PoolDense())
    sim.Projection(src1, dst, conn1, sim.PoolDense())

    sim.run(run_time)

    neo = dst.get_data()
    v = neo.segments[0].filter(name='v')[0]
    spikes = neo.segments[0].spiketrains

    sim.end()

    # TODO: check results?

    return (v, spikes)


class SingleSpikeKernelResponse(BaseTestCase):

    def check_run(self):
        (v, spikes) = do_run()

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    (v, spikes) = do_run()

    print(v)
    print(spikes)

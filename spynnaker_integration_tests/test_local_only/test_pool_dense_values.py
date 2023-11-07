# Copyright (c) 2023 The University of Manchester
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

import numpy
import pyNN.spiNNaker as sim
from pyNN.space import Grid2D
from spinnaker_testbase import BaseTestCase


def do_run():
    shape = numpy.array([10, 10])
    n_input = numpy.prod(shape)
    pool_shape = numpy.array([2, 2])
    pool_stride = numpy.array([2, 2])

    # Spike in top left, middle and bottom right
    source_spikes = [(0, 0, 0, 0), (1, 4, 4, 50), (2, 9, 9, 100)]
    n_outputs = 20
    delay = 600

    spike_array_times = [[] for _ in range(n_input)]
    kernel = numpy.array(
        [[[0 for _ in range(n_outputs)]
          for _ in range(shape[0] // pool_stride[0])]
         for _ in range(shape[1] // pool_stride[1])])
    max_time = 0
    for i, x, y, time in source_spikes:
        spike_array_times[(y * shape[0]) + x].append(time)
        kernel[x // pool_stride[0]][y // pool_stride[1]][i] = (
            4.0 * numpy.prod(pool_shape))
        max_time = max(max_time, time)

    print(kernel.shape)
    print(kernel)

    run_time = max_time + delay + 100

    sim.setup(timestep=1.)
    sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, (5, 5))
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 9)

    src = sim.Population(n_input, sim.SpikeSourceArray,
                         {'spike_times': spike_array_times},
                         label='input spikes',
                         structure=Grid2D(shape[0] / shape[1]))

    conn = sim.PoolDenseConnector(kernel, pool_stride=pool_stride,
                                  pool_shape=pool_shape)

    post_cfg = {
        'v_thresh': 1.,
        'v_reset': 0.,
        'v': 0.,
        'v_rest': 0.,
        'tau_syn_E': 1.0,
        'tau_syn_I': 1.0,
        'tau_m': 1.0
    }

    dst = sim.Population(n_outputs, sim.IF_curr_exp, post_cfg)
    dst.record('spikes')

    sim.Projection(src, dst, conn, sim.PoolDense(delay=delay))

    sim.run(run_time)

    spikes = dst.get_data("spikes").segments[0].spiketrains

    sim.end()

    expected_outputs = [(i, time + delay) for i, _, _, time in source_spikes]
    for i, time in expected_outputs:
        assert spikes[i][0].magnitude == time


class TestPoolDense(BaseTestCase):

    def check_run(self):
        do_run()

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    do_run()

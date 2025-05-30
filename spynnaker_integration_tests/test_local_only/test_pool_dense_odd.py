# Copyright (c) 2021 The University of Manchester
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

from typing import Tuple

from neo.core import AnalogSignal
from neo.core.spiketrainlist import SpikeTrainList
import numpy
import pyNN.spiNNaker as sim
from pyNN.space import Grid2D
from spinnaker_testbase import BaseTestCase


def do_run() -> Tuple[AnalogSignal, SpikeTrainList]:
    numpy.random.seed(13)

    shape = numpy.array([5, 5])
    n_input = numpy.prod(shape)

    vline = [[20. + idx // shape[1]]
             if (idx % shape[1]) == (shape[1] // 2) else []
             for idx in range(n_input)]

    vline0 = [[10. + idx // shape[1]]
              if (idx % shape[1]) == 0 else []
              for idx in range(n_input)]

    vline1 = [[5. + idx // shape[1]]
              if (idx % shape[1]) == shape[1] - 1 else []
              for idx in range(n_input)]

    print(vline)
    print(vline0)
    print(vline1)

    run_time = 60.

    sim.setup(timestep=1.)
    sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, (5, 5))
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 16)

    src = sim.Population(n_input, sim.SpikeSourceArray,
                         {'spike_times': vline},
                         label='input spikes 0',
                         structure=Grid2D(shape[0] / shape[1]))

    src1 = sim.Population(n_input, sim.SpikeSourceArray,
                          {'spike_times': vline0},
                          label='input spikes 1',
                          structure=Grid2D(shape[0] / shape[1]))

    src2 = sim.Population(n_input, sim.SpikeSourceArray,
                          {'spike_times': vline1},
                          label='input spikes 1',
                          structure=Grid2D(shape[0] / shape[1]))
    n_out = 3

    conn = sim.PoolDenseConnector([0, 200, 0], pool_shape=shape)
    conn1 = sim.PoolDenseConnector([200, 0, 0], pool_shape=shape)
    conn2 = sim.PoolDenseConnector([0, 0, 200], pool_shape=shape)

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
    sim.Projection(src2, dst, conn2, sim.PoolDense())

    sim.run(run_time)

    neo = dst.get_data()
    v = neo.segments[0].filter(name='v')[0]
    spikes = neo.segments[0].spiketrains

    sim.end()

    # TODO: check results?

    return (v, spikes)


class TestPoolDense(BaseTestCase):

    def check_run(self) -> None:
        (v, spikes) = do_run()

    def test_run(self) -> None:
        self.runsafe(self.check_run)


if __name__ == '__main__':
    (v, spikes) = do_run()

    print(v)
    print(spikes)

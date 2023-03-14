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

import numpy
import pyNN.spiNNaker as sim
from pyNN.space import Grid2D
import matplotlib.pyplot as plt
from spinnaker_testbase import BaseTestCase


def do_run(plot):
    in_shape = (11, 11)
    n_input = int(numpy.prod(in_shape))
    print("n_input ", n_input)

    # stride = numpy.array([1, 1], dtype='int32')  # h, w
    k_shape = numpy.array([5, 5], dtype='int32')
    kernel = (numpy.arange(numpy.prod(
        k_shape)) - (numpy.prod(k_shape) / 2)).reshape(k_shape) * 0.1
    print(kernel)

    run_time = 4.

    sim.setup(timestep=1.)
    sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, (5, 5))
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, (3, 3))

    spike_idx = ((in_shape[1] // 2) * in_shape[0]) + (in_shape[1] // 2)
    spike_times = [[1.0] if i == spike_idx else []
                   for i in range(n_input)]

    src = sim.Population(n_input, sim.SpikeSourceArray,
                         {'spike_times': spike_times}, label='input spikes',
                         structure=Grid2D(in_shape[0] / in_shape[1]))

    conn = sim.ConvolutionConnector(kernel)
    out_shape = conn.get_post_shape(in_shape)
    n_output = int(numpy.prod(out_shape))
    print("n_output ", n_output)

    params = {
        'v_thresh': 5.,
        'v_reset': 0.,
        'v': 0.,
        'v_rest': 0.,
        'tau_syn_E': 1.0,
        'tau_syn_I': 1.0,
        'tau_m': 1.0
    }
    output = sim.Population(n_output, sim.IF_curr_exp, params, label="out",
                            structure=Grid2D(out_shape[0] / out_shape[1]))

    output.record('v')

    sim.Projection(src, output, conn, sim.Convolution())

    sim.run(run_time)

    neo = output.get_data()

    sim.end()

    v = neo.segments[0].filter(name='v')[0]

    vmin = kernel.min()
    vmax = kernel.max()
    img = numpy.zeros(out_shape)
    for i, v_0 in enumerate(v[-1]):
        r, c = divmod(i, out_shape[0])
        img[r, c] = v_0

    if plot:
        plt.get_backend()
        plt.figure()
        ax = plt.subplot(1, 1, 1)
        ax.set_title("Voltage at end")
        im = plt.imshow(img, vmin=vmin, vmax=vmax)
        plt.colorbar(im)
        plt.show()

    ctr = img[1:-1, 1:-1].flatten()
    ker = kernel.flatten()
    kernel_ratios = ker[:-1] / ker[1:]
    ratios = ctr[:-1] / ctr[1:]

    return (ratios, kernel_ratios)


class SingleSpikeKernelResponse(BaseTestCase):

    def check_run(self):
        (ratios, kernel_ratios) = do_run(plot=False)
        is_close = numpy.isclose(ratios, kernel_ratios, rtol=0.01)
        assert (all(is_close))

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    (ratios, kernel_ratios) = do_run(plot=True)
    diff = kernel_ratios - ratios

    print(ratios)
    print(kernel_ratios)
    print(diff)
    is_close = numpy.isclose(ratios, kernel_ratios, rtol=0.01)
    print(is_close)
    assert (all(is_close))

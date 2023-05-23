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

import numpy as np
import pyNN.spiNNaker as pynn
from pyNN.space import Grid2D


def test_2d_1d():

    pynn.setup()

    neuron_type = pynn.IF_curr_exp(
        tau_m=5.0,
        cm=5.0,
        v_rest=0.0,
        v_reset=0.0,
        v_thresh=0.5,
        tau_refrac=1.0,
        i_offset=0.0,
        v=0.0,
    )

    pynn.set_number_of_neurons_per_core(pynn.IF_curr_exp, (16, 16))
    pynn.set_number_of_neurons_per_core(pynn.SpikeSourceArray, (16, 16))

    kernel = np.array(((2.0,),))

    connector = pynn.ConvolutionConnector(kernel)

    input_spikes = np.array((
        (), (), (),
        (), (), (),
        (), (), (0.0,),
    ), dtype=object)

    spike_source = pynn.SpikeSourceArray(spike_times=input_spikes)

    input_shape = (3, 3)
    input_height, input_width = input_shape
    num_neurons = input_height * input_width

    input_neurons = pynn.Population(
        num_neurons,
        spike_source,
        label='Input neurons',
        structure=Grid2D(input_width / input_height))

    output_height, output_width = connector.get_post_shape(input_shape)
    num_output_neurons = output_width * output_height

    conv_neurons = pynn.Population(
        num_output_neurons,
        neuron_type,
        label='Convolutional neurons',
        structure=Grid2D(output_width / output_height))
    conv_neurons.record("spikes")

    pynn.Projection(input_neurons, conv_neurons, connector, pynn.Convolution())

    merge_neurons = pynn.Population(
        num_output_neurons,
        neuron_type,
        label='Merge neurons')
    merge_neurons.record("spikes")

    pynn.Projection(
        conv_neurons,
        merge_neurons,
        pynn.OneToOneConnector(),
        pynn.StaticSynapse(weight=2.0))

    duration = 10
    pynn.run(duration)

    print(conv_neurons.get_data("spikes").segments[0].spiketrains)
    print(merge_neurons.get_data("spikes").segments[0].spiketrains)

    pynn.end()

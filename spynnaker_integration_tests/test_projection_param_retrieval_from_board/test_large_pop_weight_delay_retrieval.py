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

import os
from typing import Tuple

import numpy
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.models.neuron import ConnectionHolder

sources = 1000  # number of neurons in each population
targets = 2000
weight_to_spike = 2.0
delay = 1


def do_run() -> Tuple[ConnectionHolder, ConnectionHolder, ConnectionHolder,
                      ConnectionHolder, ConnectionHolder, ConnectionHolder,
                      ConnectionHolder, ConnectionHolder]:
    p.setup(timestep=1.0, min_delay=1.0)

    cell_params_lif = {'cm': 0.25,  # nF
                       'i_offset': 0.0, 'tau_m': 20.0, 'tau_refrac': 2.0,
                       'tau_syn_E': 5.0, 'tau_syn_I': 5.0, 'v_reset': -70.0,
                       'v_rest': -65.0, 'v_thresh': -50.0}

    populations = list()
    projections = list()

    populations.append(
        p.Population(sources, p.IF_curr_exp, cell_params_lif, label='pop_1'))

    populations.append(
        p.Population(targets, p.IF_curr_exp, cell_params_lif, label='pop_2'))

    connectors = p.AllToAllConnector()
    synapse_type = p.StaticSynapse(weight=weight_to_spike, delay=delay)
    projections.append(p.Projection(populations[0], populations[1],
                                    connectors, synapse_type=synapse_type))

    p.run(1)

    # before
    pre_delays_array = projections[0].get(attribute_names=["delay"],
                                          format="ndarray")
    pre_delays_list = projections[0].get(attribute_names=["delay"],
                                         format="list")
    pre_weights_array = projections[0].get(attribute_names=["weight"],
                                           format="array")
    pre_weights_list = projections[0].get(attribute_names=["weight"],
                                          format="list")

    p.run(100)

    # after
    post_delays_array = projections[0].get(attribute_names=["delay"],
                                           format="ndarray")
    post_delays_list = projections[0].get(attribute_names=["delay"],
                                          format="list")
    post_weights_array = projections[0].get(attribute_names=["weight"],
                                            format="array")
    post_weights_list = projections[0].get(attribute_names=["weight"],
                                           format="list")
    projections[0].save("weight", "test_file.txt")

    p.end()

    return (pre_delays_array, pre_delays_list, pre_weights_array,
            pre_weights_list, post_delays_array, post_delays_list,
            post_weights_array, post_weights_list)


class LargePopWeightDelayRetrival(BaseTestCase):

    def compare_before_and_after(self) -> None:
        if os.path.exists("test_file.txt"):
            os.remove("test_file.txt")
        (pre_delays_array, pre_delays_list, pre_weights_array,
            pre_weights_list, post_delays_array, post_delays_list,
            post_weights_array, post_weights_list) = do_run()
        assert os.path.isfile("test_file.txt")
        with open("test_file.txt", encoding="utf-8") as f:
            file_weights = numpy.loadtxt(f)
        np_list = numpy.array([numpy.array(wl) for wl in post_weights_list])
        np_weights = np_list.view(
                "float64").reshape((-1, 3))
        self.assertTrue(numpy.allclose(file_weights, np_weights))
        os.remove("test_file.txt")

        self.assertEqual((sources, targets), pre_delays_array.shape)
        self.assertEqual((sources, targets), pre_weights_array.shape)
        self.assertEqual((sources, targets), post_delays_array.shape)
        self.assertEqual((sources, targets), post_weights_array.shape)
        self.assertEqual(sources * targets, len(pre_delays_list))
        self.assertEqual(sources * targets, len(pre_weights_list))
        self.assertEqual(sources * targets, len(post_delays_list))
        self.assertEqual(sources * targets, len(post_weights_list))
        self.assertTrue(numpy.allclose(pre_delays_array, post_delays_array))
        self.assertTrue(numpy.allclose(pre_weights_array, post_weights_array))
        for i in range(sources*targets):
            pre_weights = pre_weights_list[i]
            assert isinstance(pre_weights, list)
            pre_weights_a = pre_weights_array[int(pre_weights[0])]
            assert isinstance(pre_weights_a, numpy.ndarray)
            self.assertEqual(pre_weights[2],
                             pre_weights_a[int(pre_weights[1])])
            pre_delays = pre_delays_list[i]
            assert isinstance(pre_delays, list)
            pre_delays_a = pre_delays_array[int(pre_delays[0])]
            assert isinstance(pre_delays_a, numpy.ndarray)
            self.assertEqual(pre_delays[2], pre_delays_a[int(pre_delays[1])])
            post_weights = post_weights_list[i]
            assert isinstance(post_weights, list)
            post_weights_a = post_weights_array[int(post_weights[0])]
            assert isinstance(post_weights_a, numpy.ndarray)
            self.assertEqual(
                post_weights[2], post_weights_a[int(post_weights[1])])
            post_delays = post_delays_list[i]
            assert isinstance(post_delays, list)
            post_delays_a = post_delays_array[int(post_delays[0])]
            assert isinstance(post_delays_a, numpy.ndarray)
            self.assertEqual(post_delays[2],
                             post_delays_a[int(post_delays[1])])

    def test_compare_before_and_after(self) -> None:
        self.runsafe(self.compare_before_and_after)

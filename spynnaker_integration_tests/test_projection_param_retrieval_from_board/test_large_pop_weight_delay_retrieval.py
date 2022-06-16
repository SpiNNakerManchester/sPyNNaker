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

import numpy
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
import os

sources = 1000  # number of neurons in each population
targets = 2000
weight_to_spike = 2.0
delay = 1


def do_run():
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
                                          format="nparray")
    pre_delays_list = projections[0].get(attribute_names=["delay"],
                                         format="list")
    pre_weights_array = projections[0].get(attribute_names=["weight"],
                                           format="array")
    pre_weights_list = projections[0].get(attribute_names=["weight"],
                                          format="list")

    p.run(100)

    # after
    post_delays_array = projections[0].get(attribute_names=["delay"],
                                           format="nparray")
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

    def compare_before_and_after(self):
        if os.path.exists("test_file.txt"):
            os.remove("test_file.txt")
        (pre_delays_array, pre_delays_list, pre_weights_array,
            pre_weights_list, post_delays_array, post_delays_list,
            post_weights_array, post_weights_list) = do_run()
        assert(os.path.isfile("test_file.txt"))
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
            self.assertEqual(pre_weights_list[i][2], pre_weights_array
                             [pre_weights_list[i][0]][pre_weights_list[i][1]])
            self.assertEqual(pre_delays_list[i][2], pre_delays_array
                             [pre_delays_list[i][0]][pre_delays_list[i][1]])
            self.assertEqual(
                post_weights_list[i][2], post_weights_array
                [post_weights_list[i][0]][post_weights_list[i][1]])
            self.assertEqual(post_delays_list[i][2], post_delays_array
                             [post_delays_list[i][0]][post_delays_list[i][1]])

    def test_compare_before_and_after(self):
        self.runsafe(self.compare_before_and_after)


if __name__ == '__main__':
    (pre_delays_array, pre_delays_list, pre_weights_array,
        pre_weights_list, post_delays_array, post_delays_list,
        post_weights_array, post_weights_list) = do_run()
    print("array")
    print(pre_delays_array.shape)
    print(pre_delays_array[0])
    print("list")
    print(len(pre_delays_list))
    print(len(pre_delays_list[0]))
    print("array")
    print(pre_weights_array.shape)
    print(pre_weights_array[0])
    print("list")
    print(len(pre_weights_list))
    print(len(pre_weights_list[0]))
    print("array")
    print(post_delays_array.shape)
    print(post_delays_array[0].shape)
    print("list")
    print(len(post_delays_list))
    print(len(post_delays_list[0]))
    print("array")
    print(post_weights_array.shape)
    print(post_weights_array[0])
    print("list")
    print(len(post_weights_list))
    print(len(post_weights_list[0]))
    with open("test_file.txt", encoding="utf-8") as f:
        print(numpy.loadtxt(f))

# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyNN.spiNNaker as sim
import numpy
from spinnaker_testbase import BaseTestCase

SOURCES = 5
DESTINATIONS = 10


class TestOneToOneConnector(BaseTestCase):

    def do_one_to_one_test(
            self, neurons_per_core, pre_size, post_size, weight, delay):
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, neurons_per_core)
        pre = sim.Population(pre_size, sim.IF_curr_exp())
        post = sim.Population(post_size, sim.IF_curr_exp())
        proj = sim.Projection(pre, post, sim.OneToOneConnector(),
                              sim.StaticSynapse(weight=weight, delay=delay))
        sim.run(0)
        conns = proj.get(["weight", "delay"], "list")
        sim.end()
        for pre, post, w, d in conns:
            assert pre == post
            assert numpy.allclose(w, weight, rtol=0.0001)
            assert d == delay

    def do_one_to_one_conductance_test(
            self, neurons_per_core, pre_size, post_size, weight, delay):
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_cond_exp, neurons_per_core)
        pre = sim.Population(pre_size, sim.IF_cond_exp())
        post = sim.Population(post_size, sim.IF_cond_exp())
        proj = sim.Projection(pre, post, sim.OneToOneConnector(),
                              sim.StaticSynapse(weight=weight, delay=delay))
        sim.run(0)
        conns = proj.get(["weight", "delay"], "list")
        sim.end()
        for pre, post, w, d in conns:
            assert pre == post
            assert numpy.allclose(w, weight, rtol=0.0001)
            assert d == delay

    def test_pre_same_as_post(self):
        self.do_one_to_one_test(10, 23, 23, 2.0, 3.0)

    def test_pre_bigger_than_post(self):
        self.do_one_to_one_test(10, 100, 23, 5.0, 1.0)

    def test_post_bigger_than_pre(self):
        self.do_one_to_one_test(10, 23, 100, 3.0, 2.0)

    def test_post_bigger_than_pre_low_weight(self):
        self.do_one_to_one_conductance_test(10, 5, 4, 0.1, 1.0)

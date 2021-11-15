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

import spynnaker8 as sim
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
            assert w == weight
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

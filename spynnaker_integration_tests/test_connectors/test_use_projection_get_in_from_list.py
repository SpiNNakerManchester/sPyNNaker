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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestUseProjectionGetInFromList(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)

        n_neurons = 10
        weights = 0.5
        delays = 7
        n_pre = 2

        p1 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop1_1')
        p2 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop1_2')

        connector_pre = sim.FixedNumberPreConnector(n_pre)

        proj_pre = sim.Projection(p1, p2, connector_pre,
                                  synapse_type=sim.StaticSynapse(
                                      weight=weights, delay=delays))

        sim.run(10)

        weights_delays_pre = proj_pre.get(["weight", "delay"], "list")

        sim.end()

        sim.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 5)

        p11 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop2_1')
        p22 = sim.Population(n_neurons, sim.IF_curr_exp, {}, label='pop2_2')

        fromlist_conn = sim.FromListConnector(weights_delays_pre)

        proj_new = sim.Projection(p11, p22, fromlist_conn)

        sim.run(10)

        weights_delays_out = proj_new.get(["weight", "delay"], "list")

        sim.end()

        self.assertCountEqual(weights_delays_pre, weights_delays_out)

    def test_use_projection_get_in_from_list(self):
        self.runsafe(self.do_run)

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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run():
    p.setup(0.1)
    runtime = 50
    populations = []

    pop_src1 = p.Population(1, p.SpikeSourceArray,
                            {'spike_times': [[5, 15, 20, 30]]}, label="src1")

    populations.append(p.Population(1, p.IF_curr_alpha, {}, label="test"))

    populations[0].set(tau_syn_E=2)
    populations[0].set(tau_syn_I=4)

    # define the projections
    p.Projection(
        pop_src1, populations[0], p.OneToOneConnector(),
        p.StaticSynapse(weight=1, delay=1), receptor_type="excitatory")
    p.Projection(
        pop_src1, populations[0], p.OneToOneConnector(),
        p.StaticSynapse(weight=1, delay=10), receptor_type="inhibitory")

    populations[0].record("all")
    p.run(runtime)
    neo = populations[0].get_data("all")
    p.end()


class TestAlpha(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_run(self):
        do_run()


if __name__ == '__main__':
    do_run()

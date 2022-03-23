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
from spinnaker_testbase import BaseTestCase
# import neo_convertor


def do_run():
    sim.setup(timestep=1)
    pop_1 = sim.Population(1, sim.IF_curr_exp, {}, label="pop_1")
    inp = sim.Population(
        1, sim.SpikeSourceArray, {'spike_times': [[0]]}, label="input")
    sim.Projection(
        pop_1, pop_1, sim.OneToOneConnector(),
        synapse_type=sim.StaticSynapse(weight=5.0, delay=1),
        receptor_type="excitatory", source=None, space=None)

    pop_1.record("spikes")
    sim.run(20)
    first_spikes = pop_1.spinnaker_get_data("spikes")

    sim.Projection(
        inp, pop_1, sim.FromListConnector([[0, 0, 5, 5]]),
        synapse_type=sim.StaticSynapse(weight=5.0, delay=1),
        receptor_type="excitatory", source=None,
        space=None)

    sim.reset()
    sim.run(20)
    second_spikes = pop_1.spinnaker_get_data("spikes")

    return first_spikes, second_spikes


class TestProjectionBetweenRun(BaseTestCase):
    def do_run(self):
        first_spikes, second_spikes = do_run()
        assert len(first_spikes) == 0
        assert len(second_spikes[0]) == 2

    def test_run(self):
        self.runsafe(self.do_run)

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

import spynnaker.plot_utils as plot_utils
import spynnaker8 as sim
from spynnaker.pyNN.utilities import neo_convertor
from p8_integration_tests.base_test_case import BaseTestCase


def do_run(seed=None):
    sim.setup(timestep=1.0, min_delay=1.0, max_delay=1.0)

    simtime = 1000

    if seed is None:
        pg_pop1 = sim.Population(2, sim.SpikeSourcePoisson(
            rate=10.0, start=0, duration=simtime), label="pg_pop1")
        pg_pop2 = sim.Population(2, sim.SpikeSourcePoisson(
            rate=10.0, start=0, duration=simtime), label="pg_pop2")
    else:
        pg_pop1 = sim.Population(2, sim.SpikeSourcePoisson(
            rate=10.0, start=0, duration=simtime),
            additional_parameters={"seed": seed}, label="pg_pop1")
        pg_pop2 = sim.Population(2, sim.SpikeSourcePoisson(
            rate=10.0, start=0, duration=simtime),
            additional_parameters={"seed": seed+1}, label="pg_pop2")

    pg_pop1.record("spikes")
    pg_pop2.record("spikes")

    sim.run(simtime)

    neo = pg_pop1.get_data("spikes")
    spikes1 = neo_convertor.convert_spikes(neo)
    neo = pg_pop2.get_data("spikes")
    spikes2 = neo_convertor.convert_spikes(neo)

    sim.end()

    return (spikes1, spikes2)


class TestPoisson(BaseTestCase):

    def test_run(self):
        (spikes1, spikes2) = do_run(self._test_seed)
        self.assertEqual(31, len(spikes1))
        self.assertEqual(15, len(spikes2))


if __name__ == '__main__':
    (spikes1, spikes2) = do_run(1)
    print(len(spikes1))
    print(spikes1)
    print(len(spikes2))
    print(spikes2)
    plot_utils.plot_spikes([spikes1, spikes2])

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

from __future__ import division
from unittest import SkipTest
from spynnaker.pyNN.exceptions import ConfigurationException
import spynnaker8 as sim
from p8_integration_tests.scripts.checker import check_data

CHIPS_PER_BOARD_EXCLUDING_SAFETY = 43.19


class ManyBoards(object):

    def add_pop(self, x, y, n_neurons, input):
        pop = sim.Population(
            n_neurons, sim.IF_curr_exp(), label="pop_{}_{}".format(x, y))
        pop.add_placement_constraint(x=x, y=y)
        sim.Projection(input, pop, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=1))
        pop.record("all")
        return pop

    def setup(self, n_boards, n_neurons, simtime):
        sim.setup(timestep=1.0, n_boards_required=n_boards)
        try:
            machine = sim.get_machine()
        except ConfigurationException as oops:
            if "Failure to detect machine " in str(oops):
                raise SkipTest("You Need at least {} boards to run this test"
                               .format(n_boards))
            raise

        input_spikes = list(range(0, simtime - 100, 10))
        self._expected_spikes = len(input_spikes)
        input = sim.Population(1, sim.SpikeSourceArray(
            spike_times=input_spikes), label="input")
        self._pops = []
        for i, chip in enumerate(machine.ethernet_connected_chips):
            if i >= n_boards:
                break
            offset = machine.BOARD_48_CHIPS[i % 48]
            x = chip.x + offset[0]
            y = chip.y + offset[1]
            # safety code in case there is a hole in the board
            if not machine.is_chip_at(x, y):
                x = chip.x
                y = chip.y
            self._pops.append(self.add_pop(x, y, n_neurons, input))

    def do_run(self, n_boards, n_neurons, simtime):
        self._simtime = simtime
        self.setup(n_boards=n_boards, n_neurons=n_neurons, simtime=simtime)
        sim.run(simtime)
        return sim

    def check_all_data(self):
        for pop in self._pops:
            check_data(pop, self._expected_spikes, self._simtime)


if __name__ == '__main__':
    """
    main entrance method
    """
    me = ManyBoards()
    run = me.do_run(n_boards=10, n_neurons=2, simtime=300)
    me.check_all_data()
    run.end()

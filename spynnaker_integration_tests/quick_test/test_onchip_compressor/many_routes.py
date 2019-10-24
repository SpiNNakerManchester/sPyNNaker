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
import math
from unittest import SkipTest
from spynnaker.pyNN.exceptions import ConfigurationException
import spynnaker as sim


def find_good_chip(machine, n_target):
    for x in range(1, 8):
        for y in range(1, 8):
            chip = machine.get_chip_at(x, y)
            if chip:
                # Must be greater than to allow the extra monitor
                if chip.n_user_processors > n_target:
                    print(chip.n_user_processors)
                    return (x, y)
    raise SkipTest("No Chip found with You Need at least {} user processors"
                   .format(n_target))


def do_run():
    n_source = 2000
    n_target = 16
    n_neurons = 1
    n_boards = math.ceil((n_source + n_target) / 16 / 48)

    sim.setup(timestep=1.0, n_boards_required=n_boards)
    try:
        machine = sim.get_machine()
    except ConfigurationException as oops:
        if "Failure to detect machine " in str(oops):
            raise SkipTest("You Need at least {} boards to run this test"
                           .format(n_boards))
        raise (oops)
    target_x, target_y = find_good_chip(machine, n_target)
    print(machine)
    print(target_x, target_y)

    sources = []
    for s in range(n_source):
        sources.append(sim.Population(n_neurons, sim.IF_curr_exp(),
                                      label="source_{}".format(s)))
    targets = []
    for t in range(n_target):
        pop = sim.Population(n_neurons, sim.IF_curr_exp(),
                             label="target_{}".format(t))
        pop.add_placement_constraint(x=target_x, y=target_y)
        targets.append(pop)

    for s in range(n_source):
        for t in range(n_target):
            sim.Projection(
                sources[s], targets[t], sim.AllToAllConnector(),
                synapse_type=sim.StaticSynapse(weight=5, delay=1),
                receptor_type="excitatory")
            if t > 1 and s % t == 0:
                sim.Projection(
                    sources[s], targets[t], sim.AllToAllConnector(),
                    synapse_type=sim.StaticSynapse(weight=5, delay=1),
                    receptor_type="inhibitory")

    sim.run(1)
    sim.end()

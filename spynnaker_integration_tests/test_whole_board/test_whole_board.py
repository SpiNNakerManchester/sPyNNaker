# Copyright (c) 2022 The University of Manchester
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


class WholeBoardTest(BaseTestCase):

    up = [(0, 0), (0, 1), (0, 2), (0, 3),
          (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
          (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
          (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
          (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
          (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
          (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
          (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)]
    down = list(up)
    down.reverse()
    right = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
             (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
             (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
             (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3),
             (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
             (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5),
             (3, 6), (4, 6), (5, 6), (6, 6), (7, 6),
             (4, 7), (5, 7), (6, 7), (7, 7)]
    left = list(right)
    left.reverse()
    ur = [(0, 0), (0, 1), (0, 2), (0, 3),
          (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
          (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
          (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
          (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
          (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
          (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
          (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)]
    dl = list(ur)
    dl.reverse()

    def find_a_placement(self):
        for count in range(17, 0, -1):
            for (x, y), processors in self.to_allocate.items():
                if processors == count:
                    if processors == 1:
                        del self.to_allocate[(x, y)]
                    else:
                        self.to_allocate[(x, y)] -= 1
                    return x, y

    def find_on_core(self, x, y):
        if (x, y) in self.to_allocate:
            self.to_allocate[(x, y)] -= 1
            if self.to_allocate[(x, y)] == 0:
                del self.to_allocate[(x, y)]
            return True
        else:
            return False

    def do_chain(self, chain, name):
        """
        Create a synfire chain register the last as the target

        :param chain:
        :param name:
        :return:
        """
        print(name, chain)
        x, y = chain.pop()
        spikeArray = {'spike_times': [[0]]}
        previous = sim.Population(
            1, sim.SpikeSourceArray, spikeArray, label=f"Stimulus {name}")
        previous.add_placement_constraint(x, y)
        for (x, y) in chain:
            current = sim.Population(
                1, sim.IF_curr_exp(), label=f"pop_{name}_{x}_{y}")
            sim.Projection(
                previous, current, sim.OneToOneConnector(),
                synapse_type=sim.StaticSynapse(weight=5, delay=1))
            current.add_placement_constraint(x, y)
            previous = current
        current.record(["spikes"])
        self.targets[name] = current

    def do_direction(self, series, name):
        """
        Create a synfire chain in this direction

        :param series:
        :param name:
        :return:
        """
        if not self.to_allocate:
            # All cores already used fine!
            return
        chain = []
        # Pick a starting outside of the chain
        x, y = self.find_a_placement()
        chain.append((x, y))
        # Add all chips in order (if possible) to use the link
        for (x, y) in series:
            if self.find_on_core(x, y):
                chain.append((x, y))
        # add and off chain target if possible
        try:
            x, y = self.find_a_placement()
            chain.append((x, y))
        except TypeError:
            pass
        # if there are only a few chips left added then to this chain
        if len(self.to_allocate) < 3:
            chain.extend(self.the_rest())
            self.to_allocate = []
        self.do_chain(chain, name)

    def the_rest(self):
        rest = []
        for (x, y), processors in self.to_allocate.items():
            for _ in range(processors):
                rest.append((x, y))
        self.to_allocate = dict()
        return rest

    def check_spikes(self):
        for name, vertex in self.targets.items():
            neo = vertex.get_data(variables=["spikes"])
            spikes = neo.segments[0].spiketrains
            print(name, spikes)
            if len(spikes) != 1:
                raise Exception("Chain {name} has {len(spikes)} spikes")

    def do_run(self):
        # find actual machine
        sim.setup(timestep=1.0, n_boards_required=1)
        machine = sim.get_machine()
        # find number of cores on machine less one for monitors
        self.to_allocate = dict()
        for key, chip in machine:
            self.to_allocate[key] = chip.n_user_processors - 1
        # less 1 for the gather
        self.to_allocate[(0, 0)] -= 1

        # keep track of the last vertex in each chain
        self.targets = dict()

        # Make synfire chains using all possible links in each direction
        self.do_direction(self.up, "up")
        self.do_direction(self.down, "down")
        self.do_direction(self.left, "left")
        self.do_direction(self.right, "right")
        self.do_direction(self.ur, "ur1")
        self.do_direction(self.dl, "dl1")
        # repeat until all cores used up
        self.do_direction(self.up, "up2")
        self.do_direction(self.down, "down2")
        self.do_direction(self.left, "left2")
        self.do_direction(self.right, "right2")
        self.do_direction(self.ur, "ur2")
        self.do_direction(self.dl, "dl2")
        self.do_direction(self.up, "up3")
        self.do_direction(self.down, "down3")
        self.do_direction(self.left, "left3")
        self.do_direction(self.right, "right3")
        self.do_direction(self.ur, "ur3")
        self.do_direction(self.dl, "dl3")
        sim.run(1000)
        self.check_spikes()
        sim.end()

    def test_run(self):
        self.runsafe(self.do_run)

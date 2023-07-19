# Copyright (c) 2022 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
import tempfile
import os
import traceback
import sys

import pyNN.spiNNaker as sim
from spinnman.spalloc import SpallocClient, SpallocState


class WholeBoardTest(object):

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
    ur = [(0, 3), (1, 4), (2, 5), (3, 6), (4, 7),
          (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7),
          (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7),
          (0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7),
          (1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6),
          (2, 0), (3, 1), (4, 2), (5, 3), (6, 4), (7, 5),
          (3, 0), (4, 1), (5, 2), (6, 3), (7, 4),
          (4, 0), (5, 1), (6, 2), (7, 3)]
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
                raise ValueError(f"Chain {name} has {len(spikes)} spikes")

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


BOARDS = [(x, y, b) for x in range(20) for y in range(20) for b in range(3)]
SPALLOC_URL = "https://spinnaker.cs.man.ac.uk/spalloc"
SPALLOC_USERNAME = "jenkins"
SPALLOC_PASSWORD = os.getenv("SPALLOC_PASSWORD")
SPALLOC_MACHINE = "SpiNNaker1M"


@pytest.mark.parametrize("x,y,b", BOARDS)
def test_run(x, y, b):
    test_dir = os.path.dirname(__file__)
    client = SpallocClient(SPALLOC_URL, SPALLOC_USERNAME, SPALLOC_PASSWORD)
    job = client.create_job_board(
        triad=(x, y, b), machine_name=SPALLOC_MACHINE)
    # Wait 30 seconds for the state to change before giving up
    # Wait for not queued for up to 30 seconds
    job.wait_for_state_change(SpallocState.QUEUED)
    # If queued or destroyed skip test
    if job.get_state() == SpallocState.QUEUED:
        job.destroy("Queued")
        pytest.skip(f"Some boards starting at {x}, {y}, {b} is in use")
    elif job.get_state() == SpallocState.DESTROYED:
        pytest.skip(f"Boards {x}, {y}, {b} could not be allocated")
    # Actually wait for ready now (as might be powering on)
    job.wait_until_ready()
    with job:
        with tempfile.TemporaryDirectory(
                prefix=f"{x}_{y}_{b}", dir=test_dir) as tmpdir:
            os.chdir(tmpdir)
            with open("spynnaker.cfg", "w", encoding="utf-8") as f:
                f.write("[Machine]\n")
                f.write("spalloc_server = None\n")
                f.write(f"machine_name = {job.get_root_host()}\n")
                f.write("version = 5\n")
            test = WholeBoardTest()
            test.do_run()


if __name__ == "__main__":
    for x, y, b in BOARDS:
        print("", file=sys.stderr,)
        print(f"*************** Testing {x}, {y}, {b} *******************",
              file=sys.stderr)
        try:
            test_run(x, y, b)
        except Exception:
            traceback.print_exc()

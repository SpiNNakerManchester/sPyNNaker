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


BOARDS = [(bx, by, bb)
          for bx in range(20)
          for by in range(20)
          for bb in range(3)]
SPALLOC_URL = "https://spinnaker.cs.man.ac.uk/spalloc"
SPALLOC_USERNAME = "jenkins"
SPALLOC_PASSWORD = os.getenv("SPALLOC_PASSWORD")
SPALLOC_MACHINE = "SpiNNaker1M"
WIDTH = 1
HEIGHT = 1
WEIGHT_TOTAL = 2.0
FIXED_PROB = 0.1


def do_run(sender_board):
    sim.setup(1.0)
    machine = sim.get_machine()

    eth_chips = list(machine.ethernet_connected_chips)
    sender = eth_chips[sender_board]
    receivers = [e for i, e in enumerate(eth_chips) if i != sender_board]

    # Create sender population big enough to fill a board
    core_count = sum(
        chip.n_user_processors - 1
        for chip in machine.get_chips_by_ethernet(sender.x, sender.y))
    sender_pop = sim.Population(
        sim.SpikeSourcePoisson.absolute_max_atoms_per_core * core_count,
        sim.SpikeSourcePoisson(rate=10), label="Sender")
    weight = WEIGHT_TOTAL / (sender_pop.size * FIXED_PROB)

    # Create and connect receivers
    receiver_pops = list()
    for eth in receivers:
        core_count = sum(
            chip.n_user_processors - 1
            for chip in machine.get_chips_by_ethernet(eth.x, eth.y))
        receiver_pop = sim.Population(
            sim.IF_curr_exp.absolute_max_atoms_per_core * core_count,
            sim.IF_curr_exp(), label=f"Receiver_{eth.x}_{eth.y}")
        receiver_pop.record("spikes")
        receiver_pops.append(receiver_pop)

        sim.Projection(
            sender_pop, receiver_pop,
            sim.FixedProbabilityConnector(FIXED_PROB),
            sim.StaticSynapse(weight=weight))

    # Run and get results
    sim.run(1000)
    all_spikes = list()
    for receiver_pop in receiver_pops:
        spikes = receiver_pop.get_data("spikes").segments[0].spiketrains
        all_spikes.append(receiver_pop, spikes)
    sim.end()

    # Check there are some spikes for every receiver
    for receiver_pop, spikes in all_spikes:
        for i, s in enumerate(spikes):
            assert len(s), f"No spikes for {receiver_pop.label}:{i}"


def run():
    do_run(sender_board=0)
    do_run(sender_board=1)
    do_run(sender_board=2)


@pytest.mark.parametrize("x,y,b", BOARDS)
def test_run(x, y, b):
    test_dir = os.path.dirname(__file__)
    client = SpallocClient(SPALLOC_URL, SPALLOC_USERNAME, SPALLOC_PASSWORD)
    job = client.create_job_rect_at_board(
        WIDTH, HEIGHT, physical=(x, y, b), machine_name=SPALLOC_MACHINE)
    # Wait 30 seconds for the state to change before giving up
    job.wait_for_state_change(SpallocState.UNKNOWN)
    if job.get_state() == SpallocState.QUEUED:
        job.destroy("Queued")
        pytest.skip(f"Some boards starting at {x}, {y}, {b} is in use")
    elif job.get_state() == SpallocState.DESTROYED:
        pytest.skip(f"Boards {x}, {y}, {b} could not be allocated")
    with job:
        with tempfile.TemporaryDirectory(
                prefix=f"{x}_{y}_{b}", dir=test_dir) as tmpdir:
            os.chdir(tmpdir)
            with open("spynnaker.cfg", "w", encoding="utf-8") as f:
                f.write("[Machine]\n")
                f.write("spalloc_server = None\n")
                f.write(f"machine_name = {job.get_root_host()}\n")
                f.write("version = 5\n")
            run()


if __name__ == "__main__":
    for b_x, b_y, b_b in BOARDS:
        print("", file=sys.stderr,)
        print(f"************* Testing {b_x}, {b_y}, {b_b} *****************",
              file=sys.stderr)
        try:
            test_run(b_x, b_y, b_b)
        except Exception:
            traceback.print_exc()

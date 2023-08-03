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
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)
from spinnman.spalloc import SpallocClient, SpallocState
from unittest.case import SkipTest


BOARDS = [(bx, by, bb, ss)
          for bx in range(20)
          for by in range(20)
          for bb in range(3)
          for ss in range(3)]
SPALLOC_URL = "https://spinnaker.cs.man.ac.uk/spalloc"
SPALLOC_USERNAME = "jenkins"
SPALLOC_PASSWORD = os.getenv("SPALLOC_PASSWORD")
SPALLOC_MACHINE = "SpiNNaker1M"
WIDTH = 1
HEIGHT = 1
POISSON_RATE = 1
WEIGHT = 2.0
FIXED_PROB = 0.1
MAX_POISSONS = 500
MAX_NEURONS = 256


def do_run(sender_board):
    sim.setup(1.0, n_boards_required=3)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, MAX_NEURONS)
    sim.set_number_of_neurons_per_core(sim.SpikeSourcePoisson, MAX_POISSONS)

    machine = sim.get_machine()

    eth_chips = list(machine.ethernet_connected_chips)
    if len(eth_chips) <= sender_board:
        raise SkipTest(
            f"Not enough boards in this set for sender {sender_board}")
    sender = eth_chips[sender_board]
    receivers = [e for i, e in enumerate(eth_chips) if i != sender_board]

    # Create sender population big enough to fill a board
    core_count = sum(
        chip.n_user_processors - 1
        for chip in machine.get_chips_by_ethernet(sender.x, sender.y)) - 1
    print(f"{core_count} cores for Poisson")
    sender_pop = sim.Population(
        MAX_POISSONS * core_count,
        sim.SpikeSourcePoisson(rate=POISSON_RATE), label="Sender")

    # Create and connect receivers
    receiver_pops = list()
    for eth in receivers:
        max_cores_per_chip = min(
            chip.n_user_processors - 1
            for chip in machine.get_chips_by_ethernet(eth.x, eth.y)) - 1
        max_cores_per_chip = min(max_cores_per_chip - 1, 14)
        n_chips = sum(1 for _ in machine.get_chips_by_ethernet(eth.x, eth.y))
        receiver_pop = sim.Population(
            MAX_NEURONS * n_chips,
            sim.IF_curr_exp(), label=f"Receiver_{eth.x}_{eth.y}",
            splitter=SplitterAbstractPopulationVertexNeuronsSynapses(
                max_cores_per_chip))
        receiver_pop.record("spikes")
        receiver_pops.append(receiver_pop)

        sim.Projection(
            sender_pop, receiver_pop,
            sim.FixedProbabilityConnector(FIXED_PROB),
            sim.StaticSynapse(weight=WEIGHT))

    # Run and get results
    sim.run(5000)
    all_spikes = list()
    for receiver_pop in receiver_pops:
        spikes = receiver_pop.get_data("spikes").segments[0].spiketrains
        all_spikes.append((receiver_pop, spikes))
    sim.end()

    # Check there are some spikes for every receiver
    for receiver_pop, spikes in all_spikes:
        for i, s in enumerate(spikes):
            assert len(s), f"No spikes for {receiver_pop.label}:{i}"


@pytest.mark.parametrize("x,y,b,s", BOARDS)
def test_run(x, y, b, s):
    test_dir = os.path.dirname(__file__)
    client = SpallocClient(SPALLOC_URL, SPALLOC_USERNAME, SPALLOC_PASSWORD)
    job = client.create_job_rect_at_board(
        WIDTH, HEIGHT, triad=(x, y, b), machine_name=SPALLOC_MACHINE)
    with job:
        job.launch_keepalive_task()
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
        with tempfile.TemporaryDirectory(
                prefix=f"{x}_{y}_{b}", dir=test_dir) as tmpdir:
            os.chdir(tmpdir)
            with open("spynnaker.cfg", "w", encoding="utf-8") as f:
                f.write("[Machine]\n")
                f.write("spalloc_server = None\n")
                f.write(f"machine_name = {job.get_root_host()}\n")
                f.write("version = 5\n")
            do_run(s)


if __name__ == "__main__":
    for b_x, b_y, b_b in BOARDS:
        for s_s in [0, 1, 2]:
            print("", file=sys.stderr,)
            print(f"************ Testing {b_x}, {b_y}, {b_b} ****************",
                  file=sys.stderr)
            try:
                test_run(b_x, b_y, b_b, s_s)
            except Exception:
                traceback.print_exc()

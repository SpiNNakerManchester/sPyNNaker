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
import logging
import numpy
from time import sleep
from shutil import rmtree

import pyNN.spiNNaker as sim
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)
from spinnman.spalloc import SpallocClient, SpallocState
from unittest.case import SkipTest


BOARDS = [(bx, by, s)
          for s in range(3)
          for a in range(2) for b in range(2)
          for bx in range(a, 20, 2) for by in range(b, 20, 2)]
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


def do_run(sender_board, job, x, y):
    sim.setup(1.0, n_boards_required=3)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, MAX_NEURONS)
    sim.set_number_of_neurons_per_core(sim.SpikeSourcePoisson, MAX_POISSONS)

    machine = sim.get_machine()

    eth_chips = list(machine.ethernet_connected_chips)
    if len(eth_chips) <= sender_board:
        raise SkipTest(
            f"Not enough boards in this set for sender {sender_board}"
            f" on boards {x}, {y} of job {job}")
    sender = eth_chips[sender_board]
    receivers = [e for i, e in enumerate(eth_chips) if i != sender_board]

    # Fill sender board with senders
    sender_pops = list()
    for chip in machine.get_chips_by_ethernet(sender.x, sender.y):
        n_cores = chip.n_user_processors - 1
        if chip == sender:
            n_cores -= 1
        sender_pop = sim.Population(
            MAX_POISSONS * n_cores, sim.SpikeSourcePoisson(rate=POISSON_RATE),
            label=f"Sender_{chip.x}_{chip.y}")
        sender_pop.add_placement_constraint(chip.x, chip.y)
        sender_pops.append(sender_pop)

    # Create and connect receivers
    receiver_pops = list()
    for eth in receivers:
        for chip in machine.get_chips_by_ethernet(eth.x, eth.y):
            n_cores = chip.n_user_processors - 1
            if chip == eth:
                n_cores -= 1
            max_cores = min(n_cores - 1, 14)
            receiver_pop = sim.Population(
                MAX_NEURONS,
                sim.IF_curr_exp(), label=f"Receiver_{chip.x}_{chip.y}",
                splitter=SplitterAbstractPopulationVertexNeuronsSynapses(
                    max_cores))
            receiver_pop.add_placement_constraint(chip.x, chip.y)
            receiver_pop.record("spikes")
            receiver_pops.append(receiver_pop)

            for sender_pop in sender_pops:
                sim.Projection(
                    sender_pop, receiver_pop,
                    sim.FixedTotalNumberConnector(
                        int(sender_pop.size * receiver_pop.size * FIXED_PROB)),
                    sim.StaticSynapse(weight=WEIGHT))

    # Run and get results
    sim.run(5000)
    all_spikes = list()
    for receiver_pop in receiver_pops:
        spikes = receiver_pop.spinnaker_get_data("spikes")
        all_spikes.append((receiver_pop, spikes))
    sim.end()

    # Check there are some spikes for every receiver
    for receiver_pop, spikes in all_spikes:
        jumps = numpy.where(numpy.diff(spikes[:, 0]) > 1)[0]
        assert len(jumps) == 0, \
            f"No spikes for {receiver_pop.label}:{spikes[:,0][jumps] + 1}"


@pytest.mark.parametrize("x,y,s", BOARDS)
def test_run(x, y, s):
    test_dir = os.path.dirname(__file__)
    client = SpallocClient(SPALLOC_URL, SPALLOC_USERNAME, SPALLOC_PASSWORD)
    job = client.create_job_rect_at_board(
        WIDTH, HEIGHT, triad=(x, y, 0), machine_name=SPALLOC_MACHINE,
        max_dead_boards=1)
    with job:
        job.launch_keepalive_task()
        # Wait for not queued for up to 30 seconds
        sleep(1.0)
        state = job.get_state(wait_for_change=True)
        # If queued or destroyed skip test
        if state == SpallocState.QUEUED:
            job.destroy("Queued")
            pytest.skip(f"Some boards starting at {x}, {y}, 0 are in use"
                        f" on job {job}")
        elif state == SpallocState.DESTROYED:
            pytest.skip(
                f"Boards {x}, {y}, 0 could not be allocated on job {job}")
        # Actually wait for ready now (as might be powering on)
        job.wait_until_ready(n_retries=3)
        print(job.get_connections())
        while job.get_root_host() is None:
            sleep(0.5)
        tmpdir = tempfile.mkdtemp(prefix=f"{x}_{y}_0", dir=test_dir)
        os.chdir(tmpdir)
        with open("spynnaker.cfg", "w", encoding="utf-8") as f:
            f.write("[Machine]\n")
            f.write("spalloc_server = None\n")
            f.write(f"machine_name = {job.get_root_host()}\n")
            f.write("version = 5\n")
            f.write("\n")
            f.write("[Reports]\n")
            f.write("write_provenance = False\n")
            f.write("read_router_provenance_data = False\n")
            f.write("read_graph_provenance_data = False\n")
            f.write("read_placements_provenance_data = False\n")
            f.write("read_profile_data = False\n")
            f.write("reports_enabled = False\n")
            f.write("write_routing_table_reports = False\n")
            f.write("write_routing_tables_from_machine_reports = False\n")
            f.write("write_tag_allocation_reports = False\n")
            f.write("write_algorithm_timings = False\n")
            f.write("write_sdram_usage_report_per_chip = False\n")
            f.write("write_partitioner_reports = False\n")
            f.write("write_application_graph_placer_report = False\n")
            f.write("write_redundant_packet_count_report = False\n")
            f.write("write_data_speed_up_reports = False\n")
            f.write("write_router_info_report = False\n")
            f.write("write_network_specification_report = False\n")
        do_run(s, job, x, y)
        # If no errors we will get here and we can remove the tree;
        # then only error folders will be left
        rmtree(tmpdir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    do_run(0, None, None, None)
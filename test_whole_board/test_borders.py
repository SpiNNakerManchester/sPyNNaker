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
import time
from shutil import rmtree

import pyNN.spiNNaker as sim
from spinnman.spalloc import SpallocClient, SpallocState


BOARDS = [(bx, by)
          for a in range(2) for b in range(2)
          for bx in range(a, 20, 2) for by in range(b, 20, 2)]
SPALLOC_URL = "https://spinnaker.cs.man.ac.uk/spalloc"
SPALLOC_USERNAME = "jenkins"
SPALLOC_PASSWORD = os.getenv("SPALLOC_PASSWORD")
SPALLOC_MACHINE = "SpiNNaker1M"
WIDTH = 2
HEIGHT = 2
POISSON_RATE = 100
WEIGHT = 100.0
MAX_NEURONS = 256


def _add_edge_chip(machine, x, y, link, edge_chips):
    if not machine.is_chip_at(x, y):
        return
    chip = machine.get_chip_at(x, y)
    lnk = chip.router.get_link(link)
    if lnk is None:
        return
    tg = machine.get_chip_at(lnk.destination_x, lnk.destination_y)
    if tg is not None:
        t00 = machine.get_chip_at(
                tg.nearest_ethernet_x, tg.nearest_ethernet_y)
        (tlx, tly) = machine.get_local_xy(tg)
        l00 = machine.get_chip_at(
                chip.nearest_ethernet_x, chip.nearest_ethernet_y)
        (lx, ly) = machine.get_local_xy(chip)
        r_link = (link + 3) % 6
        source_label = f"Sender_{x}_{y}_{link}_({lx}_{ly}_{l00.ip_address})"
        target_label = f"Target_{tg.x}_{tg.y}_{r_link}_({tlx}_{tly}"\
            + f"_{t00.ip_address})"
        edge_chips.append((chip, source_label, tg, target_label))


def _get_edge_chips(machine):
    # Walk around the edge of each board and get the chips and
    # which chips they connect to

    # See Machine FPGA links for details
    chip_links = [(7, 3, 0, 5, -1, -1),  # Bottom Right
                  (4, 0, 4, 5, -1, 0),   # Bottom
                  (0, 0, 4, 3, 0, 1),    # Left
                  (0, 3, 2, 3, 1, 1),    # Top Left
                  (4, 7, 2, 1, 1, 0),    # Top
                  (7, 7, 0, 1, 0, -1)]   # Right
    edge_chips = []
    for ethernet_connected_chip in machine.ethernet_connected_chips:
        ex = ethernet_connected_chip.x
        ey = ethernet_connected_chip.y
        for i, (x, y, l1, l2, dx, dy) in enumerate(chip_links):
            for _ in range(4):
                c_x = (x + ex) % machine.width
                c_y = (y + ey) % machine.height
                _add_edge_chip(machine, c_x, c_y, edge_chips, l1)
                if i % 2 == 1:
                    x += dx
                    y += dy
                c_x = (x + ex) % machine.width
                c_y = (y + ey) % machine.height
                _add_edge_chip(machine, c_x, c_y, edge_chips, l2)
                if i % 2 == 0:
                    x += dx
                    y += dy
    return edge_chips


def _find_missing(bigger, smaller):
    # Find where there are more of a given neuron id
    bigger_count = numpy.bincount(bigger[:, 0].astype(numpy.int32))
    smaller_count = numpy.bincount(smaller[:, 0].astype(numpy.int32))
    n_missing = bigger_count - smaller_count
    neurons_with_missing = numpy.where(n_missing > 0)[0]
    missing = dict()
    for n in neurons_with_missing:
        # Compare the timestamps of the neurons
        b = bigger[bigger[:, 0] == n][:, 1]
        s = smaller[smaller[:, 0] == n][:, 1]
        missing_times = numpy.setdiff1d(b, s)
        if len(missing_times) > 10:
            missing_times = f"{missing_times[:10]} (truncated)"
        missing[n] = missing_times
    if len(missing) > 10:
        missing = f"{len(missing)} neurons are missing data"
    return missing


def edge_test():

    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "Starting")

    sim.setup(1.0, n_boards_required=12)
    sim.set_number_of_neurons_per_core(sim.IF_curr_delta, MAX_NEURONS)
    sim.set_number_of_neurons_per_core(sim.SpikeSourcePoisson, MAX_NEURONS)

    machine = sim.get_machine()
    edge_chips = _get_edge_chips(machine)

    pops = list()
    for chip, source_label, target_chip, target_label in edge_chips:
        source = sim.Population(
            MAX_NEURONS, sim.SpikeSourcePoisson(rate=POISSON_RATE),
            label=source_label)
        source.record("spikes")
        source.add_placement_constraint(chip.x, chip.y)

        target = sim.Population(
            MAX_NEURONS, sim.IF_curr_delta(tau_refrac=0.0),
            label=target_label)
        target.record("spikes")
        target.add_placement_constraint(target_chip.x, target_chip.y)

        sim.Projection(source, target, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=WEIGHT))
        pops.append((source, target))

    # Run and get results
    sim.run(5000)

    success = True
    for source_pop, target_pop in pops:
        source_spikes = numpy.unique(
            source_pop.spinnaker_get_data("spikes"), axis=0)
        # Eliminate spikes that happened in the last timer tick
        source_spikes = source_spikes[source_spikes[:, 1] != 4999]
        # Add one to the source spike times to account for delay in targets
        source_spikes[:, 1] = source_spikes[:, 1] + 1

        # Compare with the target spikes
        target_spikes = target_pop.spinnaker_get_data("spikes")
        if (len(source_spikes) > len(target_spikes)):
            missing = _find_missing(source_spikes, target_spikes)
            print("Mismatch in sources and targets for"
                  f" {source_pop.label}->{target_pop.label}: {missing}")
            success = False
        elif (len(source_spikes) < len(target_spikes)):
            missing = _find_missing(target_spikes, source_spikes)
            print("Mismatch in targets and sources for"
                  f" {source_pop.label}->{target_pop.label}: {missing}")
            success = False
        elif not numpy.all(source_spikes[:, 0] == target_spikes[:, 0]):
            print("Mismatch in sources and targets for"
                  f" {source_pop.label}->{target_pop.label}")
            success = False
        elif not numpy.all(source_spikes[:, 1] == target_spikes[:, 1]):
            print("Mismatch in sources and targets for"
                  f" {source_pop.label}->{target_pop.label}")
            success = False
    assert success, "Something failed - see above for details"


@pytest.mark.parametrize("x,y", BOARDS)
def test_run(x, y):
    test_dir = os.path.dirname(__file__)
    client = SpallocClient(SPALLOC_URL, SPALLOC_USERNAME, SPALLOC_PASSWORD)
    job = client.create_job_rect_at_board(
        WIDTH, HEIGHT, triad=(x, y, 0), machine_name=SPALLOC_MACHINE,
        max_dead_boards=1)
    with job:
        job.launch_keepalive_task()
        # Wait for not queued for up to 30 seconds
        time.sleep(1.0)
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
            time.sleep(0.5)
        tmpdir = tempfile.mkdtemp(prefix=f"{x}_{y}_0", dir=test_dir)
        os.chdir(tmpdir)
        with open("spynnaker.cfg", "w", encoding="utf-8") as f:
            f.write("[Machine]\n")
            f.write("spalloc_server = None\n")
            f.write(f"machine_name = {job.get_root_host()}\n")
            f.write("version = 5\n")
            f.write("\n")
            f.write("[Reports]\n")
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
            f.write("write_provenance = False\n")
            f.write("read_graph_provenance_data = False\n")
            f.write("read_placements_provenance_data = False\n")
            f.write("read_profile_data = False\n")
        edge_test()
        # If no errors we will get here and we can remove the tree;
        # then only error folders will be left
        rmtree(tmpdir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    edge_test()

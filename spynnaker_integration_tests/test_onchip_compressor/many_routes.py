# Copyright (c) 2017 The University of Manchester
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
import math
from typing import Tuple

import pyNN.spiNNaker as sim

from spinn_machine import Machine

from spinn_front_end_common.interface.provenance import GlobalProvenance

from spynnaker.pyNN.exceptions import ConfigurationException
from spynnaker.pyNN import SpynnakerDataView
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterPopulationVertexFixed)


def find_good_chip(machine: Machine, n_target: int) -> Tuple[int, int]:
    for x in range(1, 8):
        for y in range(1, 8):
            chip = machine.get_chip_at(x, y)
            if chip:
                # Must be greater than to allow the extra monitor
                if chip.n_placable_processors > n_target:
                    print(chip.n_placable_processors, "processors on", x, y)
                    return (x, y)
    SpynnakerDataView.raise_skiptest(
        f"No Chip found with at least {n_target} user processors")
    raise NotImplementedError("Never reached")


def do_run() -> None:
    n_source = 1650
    n_target = 16
    n_neurons = 1
    n_boards = math.ceil((n_source + n_target) / 16 / 48)

    sim.setup(timestep=1.0, n_boards_required=n_boards)
    try:
        machine = sim.get_machine()
    except ConfigurationException as oops:
        if "Failure to detect machine " in str(oops):
            SpynnakerDataView.raise_skiptest(
                f"You Need at least {n_boards} boards to run this test", oops)
        raise oops
    target_x, target_y = find_good_chip(machine, n_target)

    targets = []
    for t in range(n_target):
        pop = sim.Population(
            n_neurons, sim.IF_curr_exp(), label="target_{}".format(t),
            additional_parameters={
                "splitter": SplitterPopulationVertexFixed()})
        pop.add_placement_constraint(x=target_x, y=target_y)
        targets.append(pop)

    sources = []
    for s in range(n_source):
        sources.append(sim.Population(
            n_neurons, sim.IF_curr_exp(), label="source_{}".format(s),
            additional_parameters={
                "splitter": SplitterPopulationVertexFixed()}))

    for s in range(n_source):
        for t in range(n_target):
            if (s + 1) % (t + 1) == 0:
                sim.Projection(
                    sources[s], targets[t], sim.AllToAllConnector(),
                    synapse_type=sim.StaticSynapse(weight=5, delay=1),
                    receptor_type="inhibitory")

    sim.run(1)
    with GlobalProvenance() as db:
        td = db.get_timer_provenance("Routing table loader")
    assert td == "", "Routing table loader should not have run"
    sim.end()

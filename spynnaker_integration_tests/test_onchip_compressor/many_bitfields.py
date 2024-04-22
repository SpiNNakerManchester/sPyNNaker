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
from spynnaker.pyNN.exceptions import ConfigurationException
import pyNN.spiNNaker as sim
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexFixed)


def find_good_chip(machine, n_target):
    for x in range(1, 8):
        for y in range(1, 8):
            chip = machine.get_chip_at(x, y)
            if chip:
                # Must be greater than to allow the extra monitor
                if chip.n_placable_processors > n_target:
                    print(chip.n_placable_processors)
                    return (x, y)
    SpynnakerDataView.raise_skiptest(
        f"No Chip found with at least {n_target} user processors")


def do_bitfield_run():
    n_source = 40
    n_target = 16
    n_neurons = 50
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

    sources = []
    for s in range(n_source):
        sources.append(sim.Population(n_neurons, sim.IF_curr_exp(),
                                      label="source_{}".format(s)))
    targets = []
    for t in range(n_target):
        pop = sim.Population(
            n_neurons, sim.IF_curr_exp(), label="target_{}".format(t),
            additional_parameters={
                "splitter": SplitterAbstractPopulationVertexFixed()})
        pop.add_placement_constraint(x=target_x, y=target_y)
        targets.append(pop)

    for s in range(n_source):
        for t in range(n_target):
            weird_list = []
            for i in range(n_neurons):
                if (s+i) % (t+1) == 0:
                    weird_list.append([i, i])
            sim.Projection(
                sources[s], targets[t], sim.FromListConnector(weird_list),
                synapse_type=sim.StaticSynapse(weight=5, delay=1),
                receptor_type="inhibitory")

    sim.run(1)
    sim.end()

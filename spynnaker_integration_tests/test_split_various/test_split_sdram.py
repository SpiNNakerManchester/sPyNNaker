# Copyright (c) 2021 The University of Manchester
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
import pyNN.spiNNaker as sim
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)
from spinnaker_testbase import BaseTestCase


def run_sdram_split():
    sim.setup(1.0)

    spikeArray = {'spike_times': []}
    pre_pop = sim.Population(
        21000, sim.SpikeSourceArray(**spikeArray), label="pre")
    post_pop = sim.Population(
        600, sim.IF_cond_exp, label="post",
        additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(
                1, 64, False)})

    pre_pop.set_max_atoms_per_core(20000)
    post_pop.set_max_atoms_per_core(64)

    sim.Projection(pre_pop, post_pop, sim.AllToAllConnector(), label="proj")

    sim.run(1000)

    sim.end()


class TestSplitSDRAM(BaseTestCase):

    def test_run_simple_split(self):
        self.runsafe(run_sdram_split)


if __name__ == "__main__":
    run_sdram_split()

# Copyright (c) 2021 The University of Manchester
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

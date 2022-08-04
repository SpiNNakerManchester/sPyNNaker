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

from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim
from .key_constraint_adder import KeyConstraintAdder


def do_run():
    sim.setup(1.0, n_boards_required=1)

    # Break up the pre population as that is where delays happen
    sim.set_number_of_neurons_per_core(sim.SpikeSourceArray, 50)
    pop1 = sim.Population(100, sim.SpikeSourceArray([1]), label="pop1")
    pop2 = sim.Population(10, sim.IF_curr_exp(), label="pop2")
    pop2.record("spikes")

    # Choose to use delay extensions
    synapse_type = sim.StaticSynapse(weight=0.5, delay=17)
    conn = sim.FixedNumberPreConnector(10)
    projection = sim.Projection(
        pop1, pop2, conn, synapse_type=synapse_type)
    delays = projection.get(["delay"], "list")

    # Run once to create what the KeyConstraintAdder needs
    sim.run(30)
    sim.reset()
    # There are 100 connections, as there are 10 for each post-neuron
    assert (len(delays) == 100)
    # If the delays are done right, all pre-spikes should arrive at the
    # same time causing each neuron in the post-population to spike
    spikes = pop2.get_data("spikes").segments[0].spiketrains
    for s in spikes:
        assert (len(s) == 1)

    # TODO work out if the KeyConstraintAdder is actually needed
    adder = KeyConstraintAdder()
    adder()
    # Now run with the KeyConstraintAdder
    # Force a hard reset
    sim.get_machine()
    sim.run(30)

    # There are 100 connections, as there are 10 for each post-neuron
    assert (len(delays) == 100)
    # If the delays are done right, all pre-spikes should arrive at the
    # same time causing each neuron in the post-population to spike
    spikes = pop2.get_data("spikes").segments[1].spiketrains
    for s in spikes:
        assert (len(s) == 1)
    sim.end()


class TestMasterPopMerges(BaseTestCase):
    # Test that a master pop table when all in edges
    # (delay and none delay could be merged)

    def test_do_run(self):
        self.runsafe(do_run)


if __name__ == "__main__":
    do_run()

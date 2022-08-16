# Copyright (c) 2017-2022 The University of Manchester
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
from spinnaker_testbase import BaseTestCase
import numpy


class TestSTDPRandomRun(BaseTestCase):
    # Test that reset with STDP and using Random weights results in the
    # same thing being loaded twice, both with data generated off and on the
    # machine

    def do_run(self):
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp(i_offset=5.0), label="pop")
        pop.record("spikes")
        pop_2 = sim.Population(1, sim.IF_curr_exp(), label="pop_2")
        proj = sim.Projection(
            pop, pop_2, sim.AllToAllConnector(),
            sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(),
                weight_dependence=sim.AdditiveWeightDependence(),
                weight=sim.RandomDistribution("uniform", low=0.3, high=0.7)))
        proj_2 = sim.Projection(
            pop, pop_2, sim.OneToOneConnector(),
            sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(),
                weight_dependence=sim.AdditiveWeightDependence(),
                weight=sim.RandomDistribution("uniform", low=0.3, high=0.7)))
        sim.run(100)
        weights_1_1 = proj.get("weight", "list")
        weights_1_2 = proj_2.get("weight", "list")
        spikes_1 = pop.get_data("spikes").segments[0].spiketrains

        sim.reset()
        sim.run(100)
        weights_2_1 = proj.get("weight", "list")
        weights_2_2 = proj_2.get("weight", "list")
        spikes_2 = pop.get_data("spikes").segments[1].spiketrains
        sim.end()

        assert numpy.array_equal(weights_1_1, weights_2_1)
        assert numpy.array_equal(weights_1_2, weights_2_2)
        assert numpy.array_equal(spikes_1, spikes_2)

    def test_do_run(self):
        self.runsafe(self.do_run)

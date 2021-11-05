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
import spynnaker8 as sim
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterPoissonDelegate, SplitterAbstractPopulationVertexNeuronsSynapses)
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from spinnaker_testbase import BaseTestCase
import numpy


def run_simple_split():
    sim.setup(0.1, time_scale_factor=1)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 16)
    # Note, this next one is ignored on one-to-one Poisson sources
    sim.set_number_of_neurons_per_core(sim.SpikeSourcePoisson, 10)

    one_to_one_source = sim.Population(
        50, sim.SpikeSourcePoisson(rate=10000), additional_parameters={
            "seed": 0,
            "splitter": SplitterPoissonDelegate()})
    rand_source = sim.Population(
        50, sim.SpikeSourcePoisson(rate=10), additional_parameters={
            "seed": 1,
            "splitter": SplitterSliceLegacy()})
    rand_source.record("spikes")
    target = sim.Population(
        50, sim.IF_curr_exp(), additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(3)})
    target.record(["spikes", "packets-per-timestep"])
    sim.Projection(
        one_to_one_source, target, sim.OneToOneConnector(),
        sim.StaticSynapse(weight=0.01))
    sim.Projection(
        rand_source, target, sim.OneToOneConnector(),
        sim.StaticSynapse(weight=2.0))

    sim.run(1000)

    source_spikes = [
        s.magnitude
        for s in rand_source.get_data("spikes").segments[0].spiketrains]
    target_spikes = [
        s.magnitude
        for s in target.get_data("spikes").segments[0].spiketrains]
    target_ppts = (numpy.nonzero(numpy.sum([
        s.magnitude
        for s in target.get_data("packets-per-timestep").segments[0].filter(
            name='packets-per-timestep')[0]], axis=1))[0] - 1) / 10

    sim.end()

    # The only actual spikes received should be from the random source
    all_source_spikes = numpy.unique(numpy.sort(numpy.concatenate(
        source_spikes)))
    assert(numpy.allclose(all_source_spikes, target_ppts))

    # A target spike should be caused by a source spike (though not all sources
    # will cause a target spike)
    for s, t in zip(source_spikes, target_spikes):
        assert(len(t) <= len(s))


class TestSplitSimple(BaseTestCase):

    def test_run_simple_split(self):
        self.runsafe(run_simple_split)


if __name__ == "__main__":
    run_simple_split()

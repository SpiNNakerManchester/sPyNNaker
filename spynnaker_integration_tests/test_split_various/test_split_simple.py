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
from spinnaker_testbase import BaseTestCase
import numpy


def run_simple_split() -> None:
    sim.setup(0.1, time_scale_factor=1)
    sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 16)
    # Note, this next one is ignored on one-to-one Poisson sources
    sim.set_number_of_neurons_per_core(sim.SpikeSourcePoisson, 10)

    one_to_one_source = sim.Population(
        50, sim.SpikeSourcePoisson(rate=10000), seed=0, label="one_to_one_src")
    rand_source = sim.Population(
        50, sim.SpikeSourcePoisson(rate=10), seed=1, label="rand_source")
    rand_source.record("spikes")
    target = sim.Population(50, sim.IF_curr_exp(), n_synapse_cores=3)
    target.record(["spikes", "packets-per-timestep"])
    target_2 = sim.Population(50, sim.IF_curr_exp(), n_synapse_cores=3)
    sim.Projection(
        one_to_one_source, target, sim.OneToOneConnector(),
        sim.StaticSynapse(weight=0.01))
    sim.Projection(
        rand_source, target, sim.OneToOneConnector(),
        sim.StaticSynapse(weight=2.0))
    sim.Projection(
        rand_source, target_2, sim.OneToOneConnector(),
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
    assert numpy.allclose(all_source_spikes, target_ppts)

    # A target spike should be caused by a source spike (though not all sources
    # will cause a target spike)
    for s, t in zip(source_spikes, target_spikes):
        assert len(t) <= len(s)


class TestSplitSimple(BaseTestCase):

    def test_run_simple_split(self) -> None:
        self.runsafe(run_simple_split)


if __name__ == "__main__":
    run_simple_split()

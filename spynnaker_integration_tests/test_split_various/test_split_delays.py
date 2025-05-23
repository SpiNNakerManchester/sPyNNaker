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
import numpy
from spinnaker_testbase import BaseTestCase


def run_delayed_split() -> None:
    sim.setup(0.1, time_scale_factor=1)
    source = sim.Population(10, sim.SpikeSourceArray(spike_times=[0]))
    target_1 = sim.Population(
        10, sim.IF_curr_exp(), label="target_1", n_synapse_cores=1)
    target_1.record("spikes")
    target_2 = sim.Population(
        10, sim.IF_curr_exp(), label="target_2", n_synapse_cores=2)
    target_2.record("spikes")
    target_3 = sim.Population(
        10, sim.IF_curr_exp(), label="target_3", n_synapse_cores=3)
    target_3.record("spikes")
    target_4 = sim.Population(
        10, sim.IF_curr_exp(), label="target_4", n_synapse_cores=3)
    target_4.record("spikes")

    # Try from list, which means host generated
    from_list = sim.Projection(source, target_1, sim.FromListConnector(
        [(a, a, 5, 0.1 + (a * 10)) for a in range(10)]))

    # Also try a couple of machine generated options
    fixed_prob = sim.Projection(
        source, target_2, sim.FixedProbabilityConnector(0.1),
        sim.StaticSynapse(weight=5.0, delay=34.0))

    # Use power-of-two to check border case
    fixed_total = sim.Projection(
        source, target_3, sim.FixedTotalNumberConnector(10),
        sim.StaticSynapse(weight=5.0, delay=2.0))

    # Try from list with power-of-two delay to check border case
    from_list_border = sim.Projection(source, target_4, sim.FromListConnector(
        [(a, a, 5, 4.0) for a in range(10)]))

    sim.run(100)

    from_list_delays = list(
        from_list.get("delay", "list", with_address=False))
    fixed_prob_delays = list(
        fixed_prob.get("delay", "list", with_address=False))
    fixed_total_delays = list(
        fixed_total.get("delay", "list", with_address=False))
    from_list_border_delays = list(
        from_list_border.get("delay", "list", with_address=False))

    from_list_spikes = [
        s.magnitude
        for s in target_1.get_data("spikes").segments[0].spiketrains]
    from_list_border_spikes = [
        s.magnitude
        for s in target_4.get_data("spikes").segments[0].spiketrains]

    sim.end()

    print(from_list_delays)
    print(from_list_spikes)
    print(fixed_prob_delays)
    print(fixed_total_delays)
    print(from_list_border_delays)
    print(from_list_border_spikes)

    # Check the delays worked out
    assert numpy.array_equal(from_list_delays,
                             [0.1 + (a * 10) for a in range(10)])
    assert all(d == 34.0 for d in fixed_prob_delays)
    assert all(d == 2.0 for d in fixed_total_delays)
    assert all(d == 4.0 for d in from_list_border_delays)

    for d, s in zip(from_list_delays, from_list_spikes):
        assert s > d
    for s in from_list_border_spikes:
        assert s > 4.0


class TestSplitDelays(BaseTestCase):

    def test_run_simple_split(self) -> None:
        self.runsafe(run_delayed_split)


if __name__ == "__main__":
    run_delayed_split()

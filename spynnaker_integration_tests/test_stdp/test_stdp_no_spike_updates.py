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

import numpy
import pyNN.spiNNaker as sim

from spinn_utilities.config_holder import set_config

from spinn_front_end_common.interface.provenance import ProvenanceReader

from spinnaker_testbase import BaseTestCase

from spynnaker.pyNN.models.neuron \
    .population_machine_synapses_provenance import STDP_PRESSURE_UPDATES


class TestSTDPNoSpikeUpdates(BaseTestCase):
    def check_weight_after_one_spike(self, n_synapse_cores: int) -> None:
        sim.setup(timestep=1.0, time_scale_factor=10)
        initial_weight = 0.125
        try:
            source = sim.Population(
                1, sim.SpikeSourceArray(spike_times=[1]), n_colour_bits=0)
            source.record("spikes")
            targets = []
            projections = []
            for budget in (0, 1):
                target = sim.Population(
                    1, sim.IF_curr_exp(i_offset=3.0),
                    n_synapse_cores=n_synapse_cores, n_colour_bits=0)
                target.record("spikes")
                dynamics = sim.STDPMechanism(
                    timing_dependence=sim.SpikePairRule(A_plus=0.05),
                    weight_dependence=sim.AdditiveWeightDependence(w_max=4.0),
                    weight=initial_weight, delay=1.0,
                    no_spike_updates_per_timestep=budget,
                    no_spike_update_capacity=1)
                projections.append(sim.Projection(
                    source, target, sim.OneToOneConnector(),
                    synapse_type=dynamics, download_synapses=True))
                targets.append(target)

            # Exercise both pause/resume and a post history that fills up.
            sim.run(25)
            sim.run(175)

            weights = [
                numpy.asarray(
                    projection.get("weight", "list", with_address=False)[0]
                ).item()
                for projection in projections]
            pre = source.get_data("spikes").segments[0].spiketrains[0]
            posts = [target.get_data("spikes").segments[0].spiketrains[0]
                     for target in targets]
            self.assertEqual(len(pre), 1)
            self.assertGreater(len(posts[0]), 15)
            self.assertGreater(posts[0].magnitude[0], pre.magnitude[0])
            numpy.testing.assert_array_equal(
                posts[0].magnitude, posts[1].magnitude)
            self.assertAlmostEqual(weights[0], initial_weight, delta=0.001)
            self.assertGreater(weights[1], weights[0] + 0.01)
        finally:
            sim.end()

    def test_combined(self) -> None:
        self.runsafe(lambda: self.check_weight_after_one_spike(0))

    def test_split(self) -> None:
        self.runsafe(lambda: self.check_weight_after_one_spike(1))

    def check_post_history_pressure(self, n_synapse_cores: int) -> None:
        sim.setup(timestep=1.0, time_scale_factor=10)
        try:
            for setting in ("write_provenance", "keep_data_database",
                            "read_placements_provenance_data",
                            "read_provenance_data_on_end"):
                set_config("Reports", setting, "True")

            # Fill the ordinary sweep with 128 rows to a quiet neuron before
            # registering the row to the fast-firing neuron. Spread the
            # first packets over four ticks to avoid testing a burst limit.
            source = sim.Population(129, sim.SpikeSourceArray(
                spike_times=[[1 + i // 32] for i in range(128)] + [[10]]),
                n_colour_bits=0)
            source.record("spikes")
            target = sim.Population(
                2, sim.IF_curr_exp(), n_synapse_cores=n_synapse_cores,
                n_colour_bits=0)
            target[1:2].set(i_offset=30.0)
            target.record("spikes")
            connections = [(i, 0) for i in range(128)] + [(128, 1)]
            dynamics = sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(
                    tau_plus=200, A_plus=0.05, A_minus=0),
                weight_dependence=sim.AdditiveWeightDependence(w_max=4),
                weight=0.0001, delay=1, no_spike_updates_per_timestep=2,
                no_spike_update_capacity=256)
            projection = sim.Projection(
                source, target, sim.FromListConnector(connections),
                synapse_type=dynamics, download_synapses=True)
            sim.run(50)

            quiet, firing = target.get_data("spikes").segments[0].spiketrains
            pre = source.get_data("spikes").segments[0].spiketrains
            self.assertEqual([len(train) for train in pre], [1] * 129)
            self.assertEqual(pre[128].magnitude[0], 10.0)
            self.assertEqual(len(quiet), 0)
            self.assertGreater(len(firing), 15)
            weights = numpy.asarray(projection.get("weight", "array"))
            numpy.testing.assert_allclose(weights[:128, 0], 0.0001, atol=0.001)
            self.assertGreater(weights[128, 1], 0.0101)
        finally:
            sim.end()

        with ProvenanceReader() as reader:
            rows = reader.run_query(
                "SELECT description, MAX(the_value) FROM core_provenance "
                "WHERE description IN (?, ?) GROUP BY description",
                (STDP_PRESSURE_UPDATES, "STDP incomplete post-event windows"))
            counters: dict[str, int] = {}
            for name, value in rows:
                if isinstance(name, str) and isinstance(value, int):
                    counters[name] = value
        self.assertGreater(counters[STDP_PRESSURE_UPDATES], 0)
        self.assertEqual(counters["STDP incomplete post-event windows"], 0)

    def test_combined_pressure(self) -> None:
        self.runsafe(lambda: self.check_post_history_pressure(0))

    def test_split_pressure(self) -> None:
        self.runsafe(lambda: self.check_post_history_pressure(1))

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
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim
import numpy
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)

# Parameters designed to make the delta neuron count spikes in voltage
PARAMS = {
    "v_rest": 0.0,
    "v_reset": 0.0,
    "v_thresh": 30000,
    "tau_refrac": 0.0,
    "tau_m": 1/(2**15),
    "cm": 1/(2**15)
}


class TestPoissonSpikeSourceSDRAM(BaseTestCase):

    def check_rate(
            self, n_neurons, v, weight, rate, spikes, seconds,
            max_spikes_per_ts, max_weight):
        runtime = seconds * 1000

        spikes_by_time = []
        for i in range(n_neurons):
            times, counts = numpy.unique(
                spikes[i].magnitude, return_counts=True)
            times = times.astype(int)
            indices = numpy.where(times < runtime - 2)[0]
            times = times[indices]
            counts = counts[indices]
            spikes_by_time.append((times, counts))

        for i in range(n_neurons):
            times, counts = spikes_by_time[i]
            vs = v.magnitude[times + 2, i]
            counts_above_max = counts > max_spikes_per_ts
            vs_where_counts_above_max = vs[counts_above_max]
            counts_below_max = counts[~counts_above_max]
            v_count_below_max = numpy.ceil(vs[~counts_above_max] / weight)

            max_mismatch = numpy.where(
                vs_where_counts_above_max != max_weight)[0]
            value_mismatch = numpy.where(
                v_count_below_max != counts_below_max)[0]

            for j in max_mismatch:
                print(f"{rate}: vs_where_counts_above_max[{i}][{j}]: "
                      f"{vs_where_counts_above_max[j]} < {max_spikes_per_ts}")
            for j in value_mismatch:
                print(f"{rate}: v_count_below_max[{j}]: "
                      f"{v_count_below_max[j]} != "
                      f"counts_below_max[{j}]: {counts_below_max[j]}")
            self.assertEqual(len(max_mismatch), 0)
            self.assertEqual(len(value_mismatch), 0)

        count = sum(len(s) for s in spikes)
        expected = rate * seconds
        tolerance = numpy.sqrt(expected)
        self.assertAlmostEqual(expected, float(count) / float(n_neurons),
                               delta=tolerance)

    def make_delta_pop(self, n_neurons, ssp, weight, delay=1.0):
        pop_1 = sim.Population(
            n_neurons, sim.IF_curr_delta(**PARAMS), label='pop_1',
            splitter=SplitterAbstractPopulationVertexNeuronsSynapses(1))
        pop_1.initialize(v=0)
        pop_1.record("v")
        proj = sim.Projection(
            ssp, pop_1, sim.OneToOneConnector(),
            sim.StaticSynapse(weight=weight, delay=delay))
        return pop_1, proj

    def recording_poisson_spikes_rate_0(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 100  # number of neurons in each population
        sim.set_number_of_neurons_per_core(sim.IF_curr_delta, n_neurons / 2)

        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {'rate': 0}, label='ssp')
        ssp.record("spikes")
        pop_1, proj = self.make_delta_pop(n_neurons, ssp, 1.0)

        sim.run(2000)
        v = pop_1.get_data("v").segments[0].filter(name='v')[0]
        spikes = ssp.get_data("spikes").segments[0].spiketrains
        conns = list(proj.get(["weight", "delay"], format="list"))
        is_poisson_direct = (
            proj._projection_edge.pre_vertex.splitter.send_over_sdram)
        sim.end()
        assert is_poisson_direct
        self.check_rate(n_neurons, v, 1.0, 0.0, spikes, 2.0, 0, 1.0)
        for i, j, w, d in conns:
            assert i == j
            assert w == 1.0
            assert d == 1.0

    def test_recording_poisson_spikes_rate_0(self):
        self.runsafe(self.recording_poisson_spikes_rate_0)

    def poisson_sdram_with_delay(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 100  # number of neurons in each population
        sim.set_number_of_neurons_per_core(sim.IF_curr_delta, n_neurons / 2)

        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {'rate': 100}, label='ssp')
        ssp.record("spikes")
        _pop_1, proj = self.make_delta_pop(n_neurons, ssp, 1.0, delay=17)

        sim.run(2000)
        conns = list(proj.get(["weight", "delay"], format="list"))
        is_poisson_direct = (
            proj._projection_edge.pre_vertex.splitter.send_over_sdram)
        sim.end()
        assert not is_poisson_direct
        # Can't really check the rate here as we expect it not use SDRAM!
        for i, j, w, d in conns:
            assert i == j
            assert w == 1.0
            assert d == 17.0

    def poisson_sdram_with_delay_different_ts(self):
        sim.setup(timestep=0.1, min_delay=1.0)
        n_neurons = 100  # number of neurons in each population
        sim.set_number_of_neurons_per_core(sim.IF_curr_delta, n_neurons / 2)

        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {'rate': 100}, label='ssp')
        ssp.record("spikes")
        _pop_1, proj = self.make_delta_pop(n_neurons, ssp, 1.0, delay=1.0)

        sim.run(2000)
        conns = list(proj.get(["weight", "delay"], format="list"))
        is_poisson_direct = (
            proj._projection_edge.pre_vertex.splitter.send_over_sdram)
        sim.end()
        assert not is_poisson_direct
        # Can't really check the rate here as we expect it not use SDRAM!
        for i, j, w, d in conns:
            assert i == j
            assert w == 1.0
            assert d == 1.0

    def test_poisson_sdram_with_delay(self):
        self.runsafe(self.poisson_sdram_with_delay)

    def check_rates(self, rates, seconds, seed):
        n_neurons = 100
        weight = 2.0
        sim.setup(timestep=1.0)
        pops = {}
        for rate in rates:
            ssp = sim.Population(
                n_neurons, sim.SpikeSourcePoisson(rate),
                label='inputSpikes_{}'.format(rate),
                additional_parameters={"seed": seed})
            ssp.record("spikes")
            target, proj = self.make_delta_pop(n_neurons, ssp, weight)
            pops[rate] = (ssp, target, proj)
        sim.run(seconds * 1000)
        v = {}
        spikes = {}
        max_spikes = {}
        max_weight = {}
        is_direct = {}
        for rate in rates:
            ssp, target, proj = pops[rate]
            v[rate] = target.get_data("v").segments[0].filter(name='v')[0]
            spikes[rate] = ssp.get_data("spikes").segments[0].spiketrains

            vtx = target._vertex
            weight_scale = vtx.get_weight_scales(
                vtx.get_ring_buffer_shifts())[0]
            max_w = 65535 / weight_scale
            max_weight[rate] = max_w
            max_spikes[rate] = int(max_w / weight)
            is_direct[rate] = (
                proj._projection_edge.pre_vertex.splitter.send_over_sdram)
        sim.end()
        for rate in rates:
            assert is_direct[rate]
            self.check_rate(
                n_neurons, v[rate], weight, rate, spikes[rate],
                seconds, max_spikes[rate], max_weight[rate])

    def recording_poisson_spikes_rate_fast(self):
        self.check_rates(
            [10.24, 20.48, 40.96, 81.92, 163.84, 327.68, 655.36, 1310.72], 10,
            0)

    def test_recording_poisson_spikes_rate_fast(self):
        self.runsafe(self.recording_poisson_spikes_rate_fast)

    def recording_poisson_spikes_rate_slow(self):
        self.check_rates(
            [0, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12],
            100, 0)

    def test_recording_poisson_spikes_rate_slow(self):
        self.runsafe(self.recording_poisson_spikes_rate_slow)

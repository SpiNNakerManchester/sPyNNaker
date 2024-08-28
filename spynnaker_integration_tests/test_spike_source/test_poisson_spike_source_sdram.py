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
import math
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

    def check_rate(self, n_neurons, v, weight, expected, spikes, runtime):
        # Check that the voltage and spike counts match
        spikes_by_time = [
            [0 for _ in range(runtime)] for _ in range(n_neurons)]
        for i in range(n_neurons):
            for s in spikes[i].magnitude:
                spikes_by_time[i][int(s)] += 1

        for i in range(n_neurons):
            for j in range(runtime - 2):
                v_i = math.ceil(v[j + 2][i] / weight)
                s_i = spikes_by_time[i][j]
                if v_i != s_i:
                    print(f"v[{i}][{j}]: {v_i} != spikes[{i}][{j}]: {s_i}")
        count_v = numpy.ceil(
            numpy.sum([numpy.sum(v_i.magnitude) for v_i in v]) / weight)
        count_spikes = sum(
            sum(1 for i in s if i < runtime - 2) for s in spikes)
        self.assertEqual(count_v, count_spikes)

        # Check that the rate is as expected
        tolerance = math.sqrt(expected)
        self.assertAlmostEqual(expected, float(count_v) / float(n_neurons),
                               delta=tolerance)

    def make_delta_pop(self, n_neurons, ssp, weight):
        pop_1 = sim.Population(
            n_neurons, sim.IF_curr_delta(**PARAMS), label='pop_1',
            splitter=SplitterAbstractPopulationVertexNeuronsSynapses(1))
        pop_1.initialize(v=0)
        pop_1.record("v")
        sim.Projection(ssp, pop_1, sim.OneToOneConnector(),
                       sim.StaticSynapse(weight=weight, delay=1.0))
        return pop_1

    def recording_poisson_spikes_rate_0(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        n_neurons = 100  # number of neurons in each population
        sim.set_number_of_neurons_per_core(sim.IF_curr_delta, n_neurons / 2)

        ssp = sim.Population(
            n_neurons, sim.SpikeSourcePoisson, {'rate': 0}, label='ssp')
        ssp.record("spikes")
        pop_1 = self.make_delta_pop(n_neurons, ssp, 1.0)

        sim.run(2000)
        v = pop_1.get_data("v").segments[0].filter(name='v')[0]
        spikes = ssp.get_data("spikes").segments[0].spiketrains
        sim.end()
        self.check_rate(n_neurons, v, 1.0, 0.0, spikes, 2000)

    def test_recording_poisson_spikes_rate_0(self):
        self.runsafe(self.recording_poisson_spikes_rate_0)

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
            target = self.make_delta_pop(n_neurons, ssp, weight)
            pops[rate] = (ssp, target)
        sim.run(seconds * 1000)
        v = {}
        spikes = {}
        for rate in rates:
            ssp, target = pops[rate]
            v[rate] = target.get_data("v").segments[0].filter(name='v')[0]
            spikes[rate] = ssp.get_data("spikes").segments[0].spiketrains
        sim.end()
        for rate in rates:
            self.check_rate(
                n_neurons, v[rate], weight, rate * seconds, spikes[rate],
                seconds * 1000)

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

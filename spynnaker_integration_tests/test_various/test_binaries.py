# Copyright (c) 2026 The University of Manchester
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

import os
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.populations import Population

INTERVAL = 50
N_NEURONS = 5


class TestBinaries(BaseTestCase):

    def add_population(self, model: AbstractPyNNModel, weight:int,
                       input_pop: Population) -> None:
        population = sim.Population(
            N_NEURONS, model, label = model.name)
        sim.Projection(input_pop, population, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=weight, delay=1))
        population.record("spikes")
        return population

    def add_neuron_population(self, model: AbstractPyNNModel, weight:int,
                              input_pop: Population) -> None:
        population = sim.Population(
            N_NEURONS, model, label = model.name, n_synapse_cores=1)
        sim.Projection(input_pop, population, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=weight, delay=1))
        population.record("spikes")
        return population

    def check_population(self, population: Population)-> None:
        neo = population.get_data(variables="spikes")
        spikes_trains = neo.segments[0].spiketrains
        print(population.label, spikes_trains)
        self.assertEqual(len(spikes_trains), N_NEURONS)
        for spike_trains in spikes_trains:
            self.assertGreaterEqual(len(spikes_trains), 1)

    def check_binaries(self) -> None:

        sim.setup(timestep=1.0)

        spike_times = []
        for i in range(N_NEURONS):
            spike_times.append([i, i + INTERVAL, i + INTERVAL * 2])
        input_pop = sim.Population(
            N_NEURONS, sim.SpikeSourceArray(spike_times=spike_times),
            label="input")

        # Ideally there should be better tests for these modules
        # remove models tested elsewhere!
        populations = []

        # IF_curr_delta_ca2_adaptive.aplx
        #populations.append(self.add_population(
        #    sim.extra_models.IFCurrDeltaCa2Adaptive(), 15, input_pop))

        # IF_curr_delta_ca2_adaptive_neuron.aplx
        #populations.append(self.add_neuron_population(
        #    sim.extra_models.IFCurrDeltaCa2Adaptive(), 15, input_pop))

        #IF_curr_exp_ca2_adaptive_stdp_mad_pair_additive.aplx

        #IF_curr_exp_dual_neuron.aplx
        #populations.append(self.add_neuron_population(
        #     sim.extra_models.IF_curr_dual_exp(), 5, input_pop))

        #IF_curr_exp_sEMD_neuron.aplx
        populations.append(self.add_population(
            sim.extra_models.IF_curr_exp_sEMD(), 15, input_pop))

        #IF_curr_exp_stdp_mad_recurrent_pre_stochastic_multiplicative.aplx
        #IZK_cond_exp_dual.aplx
        #IZK_cond_exp_dual_neuron.aplx
        #IZK_cond_exp_dual_stdp_mad_pair_additive.aplx
        #external_device_lif_control_neuron.aplx
        #synapses_stdp_izhikevich_neuromodulation_pair_additive_structural_last_neuron_distance_weight.aplx
        #synapses_stdp_izhikevich_neuromodulation_pair_multiplicative.aplx
        #synapses_stdp_izhikevich_neuromodulation_vogels_2011_additive.aplx
        #synapses_stdp_mad_nearest_pair_additive.aplx
        #synapses_stdp_mad_nearest_pair_additive_structural_random_distance_weight.aplx
        #synapses_stdp_mad_nearest_pair_multiplicative.aplx
        #synapses_stdp_mad_pair_multiplicative.aplx
        #synapses_stdp_mad_pfister_triplet_additive.aplx
        #synapses_stdp_mad_recurrent_dual_fsm_multiplicative.aplx
        #synapses_stdp_mad_vogels_2011_additive.aplx

        sim.run(N_NEURONS + INTERVAL * 3)

        for population in populations:
            self.check_population(population)
        sim.end()

        targets = SpynnakerDataView.get_executable_targets()
        binaries = set()
        for target in targets.binaries:
            _, file = os.path.split(target)
            binaries.add(file)
        print(binaries)


    def test_binaries(self) -> None:
        self.runsafe(self.check_binaries)


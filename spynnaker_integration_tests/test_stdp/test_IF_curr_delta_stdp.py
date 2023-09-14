# Copyright (c) 2023 The University of Manchester
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
import unittest
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestIFCurrDeltaSTDP(BaseTestCase):

    def mad_pair_additive_delta(self):
        timestep = 1
        spike_current = 20
        input_population_size = 2

        # Spikes set so the calculated weights for each STDP projection
        # should be identical
        spike_times1 = [[1,27,55], [1,27,55]]
        spike_times2 = [[1,33,59], [1,33,59]]
        training_times = [28]
        save_spike_times = [90]
        runtime = save_spike_times[-1] + 10

        sim.setup(timestep=timestep)

        IF_curr_delta_model = sim.IF_curr_delta()

        # Set up populations
        ssa1 = sim.Population(
            input_population_size, sim.SpikeSourceArray(spike_times1),
            label='ssa1')
        ssa2 = sim.Population(
            input_population_size, sim.SpikeSourceArray(spike_times2),
            label='ssa2')
        save_neuron = sim.Population(
            1, sim.SpikeSourceArray(save_spike_times), label='save_neuron')
        injector_neurons_exc = sim.Population(
            input_population_size, IF_curr_delta_model,
            label='injector_neurons_exc')
        injector_neurons_inh = sim.Population(
            input_population_size, IF_curr_delta_model,
            label='injector_neurons_inh')
        teacher_population = sim.Population(
            1, sim.SpikeSourceArray(training_times),
            label='teacher_population')
        output_neuron = sim.Population(
            1, IF_curr_delta_model, label='output_neuron')

        # Set up projections
        static_synapse = sim.StaticSynapse(weight=spike_current, delay=1)
        teaching_synapse = sim.StaticSynapse(weight=spike_current, delay=2)

        # SSA -> injectors
        sim.Projection(
            ssa1, injector_neurons_exc, sim.OneToOneConnector(),
            static_synapse, receptor_type='excitatory')
        sim.Projection(
            ssa2, injector_neurons_inh, sim.OneToOneConnector(),
            static_synapse, receptor_type='excitatory')

        # save -> injectors
        sim.Projection(save_neuron, injector_neurons_exc,
                       sim.AllToAllConnector(allow_self_connections=True),
                       static_synapse, receptor_type='excitatory')
        sim.Projection(save_neuron, injector_neurons_inh,
                       sim.AllToAllConnector(allow_self_connections=True),
                       static_synapse, receptor_type='excitatory')

        # teacher -> output
        sim.Projection(teacher_population, output_neuron,
                       sim.AllToAllConnector(allow_self_connections=True),
                       teaching_synapse, receptor_type='excitatory')

        # stdp models for injector -> output
        stdp_model = sim.STDPMechanism(
            timing_dependence=sim.SpikePairRule(
                tau_plus=10, tau_minus=12, A_plus=1, A_minus=-1),
            weight_dependence=sim.AdditiveWeightDependence(w_min=0, w_max=20),
            weight=0, delay=1)
        stdp_model2 = sim.STDPMechanism(
            timing_dependence=sim.SpikePairRule(
                tau_plus=10, tau_minus=12, A_plus=1, A_minus=-1),
            weight_dependence=sim.AdditiveWeightDependence(w_min=0, w_max=20),
            weight=0, delay=1)

        injector_proj_exc = sim.Projection(
            injector_neurons_exc, output_neuron,
            sim.AllToAllConnector(allow_self_connections=True),
            stdp_model, receptor_type='excitatory')
        injector_proj_inh = sim.Projection(
            injector_neurons_inh, output_neuron,
            sim.AllToAllConnector(allow_self_connections=True),
            stdp_model2, receptor_type='inhibitory')

        sim.run(runtime)

        weights_exc = injector_proj_exc.get(["weight"], "list")
        weights_inh = injector_proj_inh.get(["weight"], "list")

        print(weights_exc)
        print(weights_inh)

        sim.end()

        self.assertTrue(numpy.allclose(weights_exc, weights_inh, rtol=0.001))

    def nearest_pair_additive_delta(self):
        timestep = 1
        spike_current = 20
        input_population_size = 2

        # Spikes set so the calculated weights for each STDP projection
        # should be identical
        spike_times1 = [[1,27,51], [1,27,51]]
        spike_times2 = [[1,33,60], [1,33,60]]
        training_times = [28]
        save_spike_times = [90]
        runtime = save_spike_times[-1] + 10

        sim.setup(timestep=timestep)

        IF_curr_delta_model = sim.IF_curr_delta()

        # Set up populations
        ssa1 = sim.Population(
            input_population_size, sim.SpikeSourceArray(spike_times1),
            label='ssa1')
        ssa2 = sim.Population(
            input_population_size, sim.SpikeSourceArray(spike_times2),
            label='ssa2')
        save_neuron = sim.Population(
            1, sim.SpikeSourceArray(save_spike_times), label='save_neuron')
        injector_neurons_exc = sim.Population(
            input_population_size, IF_curr_delta_model,
            label='injector_neurons_exc')
        injector_neurons_inh = sim.Population(
            input_population_size, IF_curr_delta_model,
            label='injector_neurons_inh')
        teacher_population = sim.Population(
            1, sim.SpikeSourceArray(training_times),
            label='teacher_population')
        output_neuron = sim.Population(
            1, IF_curr_delta_model, label='output_neuron')

        # Set up projections
        static_synapse = sim.StaticSynapse(weight=spike_current, delay=1)
        teaching_synapse = sim.StaticSynapse(weight=spike_current, delay=2)

        # SSA -> injectors
        sim.Projection(
            ssa1, injector_neurons_exc, sim.OneToOneConnector(),
            static_synapse, receptor_type='excitatory')
        sim.Projection(
            ssa2, injector_neurons_inh, sim.OneToOneConnector(),
            static_synapse, receptor_type='excitatory')

        # save -> injectors
        sim.Projection(save_neuron, injector_neurons_exc,
                       sim.AllToAllConnector(allow_self_connections=True),
                       static_synapse, receptor_type='excitatory')
        sim.Projection(save_neuron, injector_neurons_inh,
                       sim.AllToAllConnector(allow_self_connections=True),
                       static_synapse, receptor_type='excitatory')

        # teacher -> output
        sim.Projection(teacher_population, output_neuron,
                       sim.AllToAllConnector(allow_self_connections=True),
                       teaching_synapse, receptor_type='excitatory')

        # stdp models for injector -> output
        stdp_model = sim.STDPMechanism(
            timing_dependence=sim.extra_models.SpikeNearestPairRule(
                tau_plus=10, tau_minus=12, A_plus=1, A_minus=-1),
            weight_dependence=sim.AdditiveWeightDependence(w_min=0, w_max=20),
            weight=0, delay=1)
        stdp_model2 = sim.STDPMechanism(
            timing_dependence=sim.extra_models.SpikeNearestPairRule(
                tau_plus=10, tau_minus=12, A_plus=1, A_minus=-1),
            weight_dependence=sim.AdditiveWeightDependence(w_min=0, w_max=20),
            weight=0, delay=1)

        injector_proj_exc = sim.Projection(
            injector_neurons_exc, output_neuron,
            sim.AllToAllConnector(allow_self_connections=True),
            stdp_model, receptor_type='excitatory')
        injector_proj_inh = sim.Projection(
            injector_neurons_inh, output_neuron,
            sim.AllToAllConnector(allow_self_connections=True),
            stdp_model2, receptor_type='inhibitory')

        sim.run(runtime)

        weights_exc = injector_proj_exc.get(["weight"], "list")
        weights_inh = injector_proj_inh.get(["weight"], "list")

        print(weights_exc)
        print(weights_inh)

        sim.end()

        self.assertTrue(numpy.allclose(weights_exc, weights_inh, rtol=0.001))

    def test_mad_pair_additive_delta(self):
        self.runsafe(self.mad_pair_additive_delta)

    def test_nearest_pair_additive_delta(self):
        self.runsafe(self.nearest_pair_additive_delta)


if __name__ == '__main__':
    unittest.main()

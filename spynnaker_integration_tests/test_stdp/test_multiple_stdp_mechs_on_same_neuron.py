#!/usr/bin/python

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

from spynnaker.pyNN.exceptions import SynapticConfigurationException
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestMultipleStdpMechsOnSameNeuron(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """
    def run_multiple_stdp_mechs_on_same_neuron(self) -> None:
        p.setup(timestep=1.0, min_delay=1.0)
        nNeurons = 200  # number of neurons in each population

        cell_params_lif = {'cm': 0.25, 'i_offset': 0.0, 'tau_m': 20.0,
                           'tau_refrac': 2.0, 'tau_syn_E': 5.0,
                           'tau_syn_I': 5.0, 'v_reset': -70.0, 'v_rest': -65.0,
                           'v_thresh': -50.0}

        populations = list()
        projections = list()

        weight_to_spike = 2.0
        delay = 1

        connections = list()
        for i in range(0, nNeurons):
            singleConnection = (i, ((i + 1) % nNeurons), weight_to_spike,
                                delay)
            connections.append(singleConnection)

        # Plastic Connection between pre_pop and post_pop
        stdp_model1 = p.STDPMechanism(
            timing_dependence=p.SpikePairRule(
                tau_plus=16.7, tau_minus=33.7, A_plus=0.005, A_minus=0.005),
            weight_dependence=p.AdditiveWeightDependence(
                w_min=0.0, w_max=1.0),
        )

        # Plastic Connection between pre_pop and post_pop
        stdp_model2 = p.STDPMechanism(
            timing_dependence=p.SpikePairRule(
                tau_plus=16.7, tau_minus=33.7, A_plus=0.005, A_minus=0.005),
            weight_dependence=p.AdditiveWeightDependence(
                w_min=0.0, w_max=1.0),
        )

        # Plastic Connection between pre_pop and post_pop
        stdp_model3 = p.STDPMechanism(
            timing_dependence=p.SpikePairRule(
                tau_plus=16.7, tau_minus=33.7, A_plus=0.005, A_minus=0.005),
            weight_dependence=p.MultiplicativeWeightDependence(
                w_min=0.0, w_max=1.0),
        )

        injectionConnection = [(0, 0, weight_to_spike, 1)]
        spikeArray1 = {'spike_times': [[0]]}
        spikeArray2 = {'spike_times': [[25]]}
        spikeArray3 = {'spike_times': [[50]]}
        spikeArray4 = {'spike_times': [[75]]}
        spikeArray5 = {'spike_times': [[100]]}
        spikeArray6 = {'spike_times': [[125]]}
        spikeArray7 = {'spike_times': [[150]]}
        spikeArray8 = {'spike_times': [[175]]}

        populations.append(p.Population(nNeurons,
                                        p.IF_curr_exp(**cell_params_lif),
                                        label='pop_1'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray1),
                                        label='inputSpikes_1'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray2),
                                        label='inputSpikes_2'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray3),
                                        label='inputSpikes_3'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray4),
                                        label='inputSpikes_4'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray5),
                                        label='inputSpikes_5'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray6),
                                        label='inputSpikes_6'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray7),
                                        label='inputSpikes_7'))
        populations.append(p.Population(1, p.SpikeSourceArray(**spikeArray8),
                                        label='inputSpikes_8'))

        projections.append(p.Projection(populations[0], populations[0],
                                        p.FromListConnector(connections),
                                        p.StaticSynapse(weight=weight_to_spike,
                                                        delay=delay)))
        pop = p.Projection(populations[1], populations[0],
                           p.FromListConnector(injectionConnection),
                           p.StaticSynapse(weight=weight_to_spike, delay=1))
        projections.append(pop)

        pop = p.Projection(populations[2], populations[0],
                           p.FromListConnector(injectionConnection),
                           synapse_type=stdp_model1)
        projections.append(pop)

        # This is expected to raise a SynapticConfigurationException
        pop = p.Projection(populations[3], populations[0],
                           p.FromListConnector(injectionConnection),
                           synapse_type=stdp_model2)
        projections.append(pop)

        pop = p.Projection(populations[4], populations[0],
                           p.FromListConnector(injectionConnection),
                           synapse_type=stdp_model3)
        projections.append(pop)

    def test_multiple_stdp_mechs_on_same_neuron(self) -> None:
        with self.assertRaises(SynapticConfigurationException):
            self.runsafe(self.run_multiple_stdp_mechs_on_same_neuron)
        # We have to end here as the exception happens before end
        p.end()

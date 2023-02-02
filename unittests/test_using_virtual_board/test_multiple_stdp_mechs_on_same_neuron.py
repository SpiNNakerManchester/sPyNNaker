#!/usr/bin/python

# Copyright (c) 2017-2019 The University of Manchester
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

"""
Synfirechain-like example
"""
import unittest
from spynnaker.pyNN.exceptions import SynapticConfigurationException
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestMultipleStdpMechsOnSameNeuron(BaseTestCase):
    """
    tests the get spikes given a simulation at 0.1 ms time steps
    """

    # NO unittest_setup() as sim.setup is called

    def run_multiple_stdp_mechs_on_same_neuron(self, mode="same"):
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
        if mode == "same":
            stdp_model3 = p.STDPMechanism(
                timing_dependence=p.SpikePairRule(
                    tau_plus=16.7, tau_minus=33.7, A_plus=0.005,
                    A_minus=0.005),
                weight_dependence=p.AdditiveWeightDependence(
                    w_min=0.0, w_max=1.0),
            )
        elif mode == "weight_dependence":
            stdp_model3 = p.STDPMechanism(
                timing_dependence=p.SpikePairRule(
                    tau_plus=16.7, tau_minus=33.7, A_plus=0.005,
                    A_minus=0.005),
                weight_dependence=p.MultiplicativeWeightDependence(
                    w_min=0.0, w_max=1.0),
            )
        elif mode == "tau":
            stdp_model3 = p.STDPMechanism(
                timing_dependence=p.SpikePairRule(
                    tau_plus=15.7, tau_minus=33.7, A_plus=0.005,
                    A_minus=0.005),
                weight_dependence=p.AdditiveWeightDependence(
                    w_min=0.0, w_max=1.0),
            )
        elif mode == "wmin":
            stdp_model3 = p.STDPMechanism(
                timing_dependence=p.SpikePairRule(
                    tau_plus=16.7, tau_minus=33.7, A_plus=0.005,
                    A_minus=0.005),
                weight_dependence=p.AdditiveWeightDependence(w_min=1.0,
                                                             w_max=1.0), )
        else:
            raise ValueError(mode)

        injectionConnection = [(0, 0, weight_to_spike, 1)]
        spikeArray1 = {'spike_times': [[0]]}
        spikeArray2 = {'spike_times': [[25]]}
        spikeArray3 = {'spike_times': [[50]]}
        spikeArray4 = {'spike_times': [[75]]}
        spikeArray5 = {'spike_times': [[100]]}
        spikeArray6 = {'spike_times': [[125]]}
        spikeArray7 = {'spike_times': [[150]]}
        spikeArray8 = {'spike_times': [[175]]}

        populations.append(p.Population(nNeurons, p.IF_curr_exp,
                                        cell_params_lif,
                                        label='pop_1'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray1,
                                        label='inputSpikes_1'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray2,
                                        label='inputSpikes_2'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray3,
                                        label='inputSpikes_3'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray4,
                                        label='inputSpikes_4'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray5,
                                        label='inputSpikes_5'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray6,
                                        label='inputSpikes_6'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray7,
                                        label='inputSpikes_7'))
        populations.append(p.Population(1, p.SpikeSourceArray, spikeArray8,
                                        label='inputSpikes_8'))

        projections.append(p.Projection(populations[0], populations[0],
                                        p.FromListConnector(connections)))
        pop = p.Projection(populations[1], populations[0],
                           p.FromListConnector(injectionConnection))
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

    def test_test_multiple_stdp_mechs_on_same_neuron(self):
        self.run_multiple_stdp_mechs_on_same_neuron(mode="same")

    def test_weight_dependence(self):
        with self.assertRaises(SynapticConfigurationException):
            self.run_multiple_stdp_mechs_on_same_neuron(
                mode="weight_dependence")

    def test_wmin(self):
        with self.assertRaises(SynapticConfigurationException):
            self.run_multiple_stdp_mechs_on_same_neuron(
                mode="wmin")

    def test_tau(self):
        with self.assertRaises(SynapticConfigurationException):
            self.run_multiple_stdp_mechs_on_same_neuron(
                mode="tau")


if __name__ == '__main__':
    unittest.main()

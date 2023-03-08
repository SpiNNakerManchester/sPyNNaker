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
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    calculate_spike_pair_additive_stdp_weight)
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as p
import numpy
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertexNeuronsSynapses)


def split_structural_with_stdp():
    p.setup(1.0)
    pre_spikes = numpy.array(range(0, 10, 2))
    pre_spikes_last_neuron = pre_spikes[pre_spikes > 0]
    A_plus = 0.01
    A_minus = 0.01
    tau_plus = 20.0
    tau_minus = 20.0
    w_min = 0.0
    w_max = 5.0
    w_init_1 = 5.0
    delay_1 = 2.0
    w_init_2 = 4.0
    delay_2 = 1.0
    stim = p.Population(1, p.SpikeSourceArray(pre_spikes), label="stim")
    pop = p.Population(
        1, p.IF_curr_exp(), label="pop", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})
    pop_2 = p.Population(
        1, p.IF_curr_exp(), label="pop_2", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})
    pop_3 = p.Population(
        1, p.IF_curr_exp(), label="pop_3", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})
    pop_4 = p.Population(
        1, p.IF_curr_exp(), label="pop_4", additional_parameters={
            "splitter": SplitterAbstractPopulationVertexNeuronsSynapses(1)})
    pop.record("spikes")
    pop_2.record("spikes")
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), p.StructuralMechanismSTDP(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 1.0),
            elimination=p.RandomByWeightElimination(2.0, 0, 0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=w_init_1, initial_delay=delay_1,
            s_max=1, seed=0, weight=0.0, delay=1.0))
    proj_2 = p.Projection(
        stim, pop_2, p.FromListConnector([]), p.StructuralMechanismSTDP(
            partner_selection=p.RandomSelection(),
            formation=p.DistanceDependentFormation([1, 1], 1.0),
            elimination=p.RandomByWeightElimination(4.0, 0, 0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=w_init_2, initial_delay=delay_2,
            s_max=1, seed=0, weight=0.0, delay=1.0))
    proj_3 = p.Projection(
        stim, pop_3, p.FromListConnector([(0, 0)]),
        p.StructuralMechanismSTDP(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=2.0, initial_delay=5.0,
            s_max=1, seed=0, weight=0.0, delay=1.0))
    proj_4 = p.Projection(
        stim, pop_4, p.FromListConnector([(0, 0)]),
        p.StructuralMechanismSTDP(
            partner_selection=p.RandomSelection(),
            formation=p.DistanceDependentFormation([1, 1], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=4.0, initial_delay=3.0,
            s_max=1, seed=0, weight=0.0, delay=1.0))
    p.run(10)

    conns = list(proj.get(["weight", "delay"], "list"))
    conns_2 = list(proj_2.get(["weight", "delay"], "list"))
    conns_3 = list(proj_3.get(["weight", "delay"], "list"))
    conns_4 = list(proj_4.get(["weight", "delay"], "list"))

    spikes_1 = [s.magnitude
                for s in pop.get_data("spikes").segments[0].spiketrains]
    spikes_2 = [s.magnitude
                for s in pop_2.get_data("spikes").segments[0].spiketrains]

    p.end()

    print(conns)
    print(conns_2)
    print(conns_3)
    print(conns_4)

    w_final_1 = calculate_spike_pair_additive_stdp_weight(
        pre_spikes_last_neuron, spikes_1[0], w_init_1, delay_1,
        A_plus, A_minus, tau_plus, tau_minus)
    w_final_2 = calculate_spike_pair_additive_stdp_weight(
        pre_spikes, spikes_2[0], w_init_2, delay_2, A_plus, A_minus,
        tau_plus, tau_minus)
    print(w_final_1, spikes_1[0])
    print(w_final_2, spikes_2[0])

    assert len(conns) == 1
    assert conns[0][3] == delay_1
    assert (conns[0][2] >= w_final_1 - 0.01 and
            conns[0][2] <= w_final_1 + 0.01)
    assert len(conns_2) == 1
    assert conns_2[0][3] == delay_2
    assert (conns_2[0][2] >= w_final_2 - 0.01 and
            conns_2[0][2] <= w_final_2 + 0.01)
    assert len(conns_3) == 0
    assert len(conns_4) == 0


class TestStructuralWithSTDP(BaseTestCase):

    def test_split_structural_with_stdp(self):
        self.runsafe(split_structural_with_stdp)

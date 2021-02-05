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
from p8_integration_tests.base_test_case import (
    BaseTestCase, calculate_spike_pair_additive_stdp_weight)
import spynnaker8 as p
import numpy


def structural_with_stdp():
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
    pop = p.Population(1, p.IF_curr_exp(), label="pop")
    pop_2 = p.Population(1, p.IF_curr_exp(), label="pop_2")
    pop_3 = p.Population(1, p.IF_curr_exp(), label="pop_3")
    pop_4 = p.Population(1, p.IF_curr_exp(), label="pop_4")
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
        pre_spikes_last_neuron, spikes_1[0], w_init_1, delay_1, w_max,
        A_plus, A_minus, tau_plus, tau_minus)
    w_final_2 = calculate_spike_pair_additive_stdp_weight(
        pre_spikes, spikes_2[0], w_init_2, delay_2, w_max, A_plus, A_minus,
        tau_plus, tau_minus)
    print(w_final_1, spikes_1[0])
    print(w_final_2, spikes_2[0])

    assert(len(conns) == 1)
    assert(conns[0][3] == delay_1)
    assert(conns[0][2] >= w_final_1 - 0.01 and
           conns[0][2] <= w_final_1 + 0.01)
    assert(len(conns_2) == 1)
    assert(conns_2[0][3] == delay_2)
    assert(conns_2[0][2] >= w_final_2 - 0.01 and
           conns_2[0][2] <= w_final_2 + 0.01)
    assert(len(conns_3) == 0)
    assert(len(conns_4) == 0)


class TestStructuralWithSTDP(BaseTestCase):

    def test_structural_with_stdp(self):
        self.runsafe(structural_with_stdp)


if __name__ == "__main__":
    structural_with_stdp()

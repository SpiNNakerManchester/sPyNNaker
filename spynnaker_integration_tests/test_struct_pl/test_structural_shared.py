# Copyright (c) 2017-2022 The University of Manchester
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

from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    calculate_spike_pair_additive_stdp_weight)
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as p
import numpy


def structural_shared():
    p.setup(1.0)
    pre_spikes = numpy.array(range(0, 10, 2))
    A_plus = 0.01
    A_minus = 0.01
    tau_plus = 20.0
    tau_minus = 20.0
    w_min = 0.0
    w_max = 5.0
    w_init = 5.0
    w_init_stdp = 2.0
    delay_init = 2.0
    delay_init_stdp = 5.0
    stim = p.Population(1, p.SpikeSourceArray(pre_spikes), label="stim")
    pop = p.Population(1, p.IF_curr_exp(), label="pop")
    pop_2 = p.Population(1, p.IF_curr_exp(), label="pop_2")
    pop_3 = p.Population(1, p.IF_curr_exp(), label="pop_3")
    pop_4 = p.Population(1, p.IF_curr_exp(), label="pop_4")
    pop.record("spikes")
    pop_3.record("spikes")
    struct_pl_static_form = p.StructuralMechanismStatic(
        partner_selection=p.LastNeuronSelection(),
        formation=p.DistanceDependentFormation([1, 1], 1.0),
        elimination=p.RandomByWeightElimination(2.0, 0, 0),
        f_rew=1000, initial_weight=w_init, initial_delay=delay_init,
        s_max=1, seed=0, weight=0.0, delay=1.0)
    struct_pl_static_elim = p.StructuralMechanismStatic(
        partner_selection=p.LastNeuronSelection(),
        formation=p.DistanceDependentFormation([1, 1], 0.0),
        elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
        f_rew=1000, initial_weight=w_init, initial_delay=delay_init,
        s_max=1, seed=0, weight=0.0, delay=1.0)
    struct_pl_stdp_form = p.StructuralMechanismSTDP(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 1.0),
            elimination=p.RandomByWeightElimination(2.0, 0, 0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=w_init_stdp,
            initial_delay=delay_init_stdp,
            s_max=1, seed=0, weight=0.0, delay=1.0)
    struct_pl_stdp_elim = p.StructuralMechanismSTDP(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=w_init_stdp,
            initial_delay=delay_init_stdp,
            s_max=1, seed=0, weight=0.0, delay=1.0)
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), struct_pl_static_form)
    proj_2 = p.Projection(
        stim, pop_2, p.FromListConnector([(0, 0)]), struct_pl_static_elim)
    proj_3 = p.Projection(
        stim, pop_3, p.FromListConnector([]), struct_pl_stdp_form)
    proj_4 = p.Projection(
        stim, pop_4, p.FromListConnector([(0, 0)]), struct_pl_stdp_elim)
    p.Projection(pop_3, pop_4, p.AllToAllConnector(),
                 p.StaticSynapse(weight=1, delay=3))
    p.run(10)

    conns = list(proj.get(["weight", "delay"], "list"))
    conns_2 = list(proj_2.get(["weight", "delay"], "list"))
    conns_3 = list(proj_3.get(["weight", "delay"], "list"))
    conns_4 = list(proj_4.get(["weight", "delay"], "list"))

    spikes_3 = [s.magnitude
                for s in pop_3.get_data("spikes").segments[0].spiketrains]
    p.end()

    print(conns)
    print(conns_2)
    print(conns_3)
    print(conns_4)

    w_final_1 = calculate_spike_pair_additive_stdp_weight(
        pre_spikes, spikes_3[0], w_init_stdp, delay_init_stdp,
        A_plus, A_minus, tau_plus, tau_minus)

    assert(len(conns) == 1)
    assert(conns[0][2] >= w_init - 0.01 and
           conns[0][2] <= w_init + 0.01)
    assert(len(conns_2) == 0)
    assert(len(conns_3) == 1)
    assert(conns_3[0][2] >= w_final_1 - 0.01 and
           conns_3[0][2] <= w_final_1 + 0.01)
    assert(len(conns_4) == 0)


class TestStructuralShared(BaseTestCase):

    def test_structural_shared(self):
        self.runsafe(structural_shared)


if __name__ == "__main__":
    structural_shared()

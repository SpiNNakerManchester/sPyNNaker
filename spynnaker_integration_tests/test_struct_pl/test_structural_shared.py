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
from spinnaker_testbase import BaseTestCase
import spynnaker8 as p
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
    delay_init = 2.0
    stim = p.Population(1, p.SpikeSourceArray(pre_spikes), label="stim")
    pop = p.Population(1, p.IF_curr_exp(), label="pop")
    pop_2 = p.Population(1, p.IF_curr_exp(), label="pop_2")
    pop_3 = p.Population(1, p.IF_curr_exp(), label="pop_3")
    pop_4 = p.Population(1, p.IF_curr_exp(), label="pop_4")
    pop.record("spikes")
    pop_2.record("spikes")
    struct_pl_static = p.StructuralMechanismStatic(
        partner_selection=p.LastNeuronSelection(),
        formation=p.DistanceDependentFormation([1, 1], 1.0),
        elimination=p.RandomByWeightElimination(2.0, 0, 0),
        f_rew=1000, initial_weight=w_init, initial_delay=delay_init,
        s_max=1, seed=0, weight=0.0, delay=1.0)
    struct_pl_stdp = p.StructuralMechanismSTDP(
            partner_selection=p.LastNeuronSelection(),
            formation=p.DistanceDependentFormation([1, 1], 0.0),
            elimination=p.RandomByWeightElimination(4.0, 1.0, 1.0),
            timing_dependence=p.SpikePairRule(
                tau_plus, tau_minus, A_plus, A_minus),
            weight_dependence=p.AdditiveWeightDependence(w_min, w_max),
            f_rew=1000, initial_weight=2.0, initial_delay=5.0,
            s_max=1, seed=0, weight=0.0, delay=1.0)
    proj = p.Projection(
        stim, pop, p.FromListConnector([]), struct_pl_static)
    proj_2 = p.Projection(
        stim, pop_2, p.FromListConnector([]), struct_pl_static)
    proj_3 = p.Projection(
        stim, pop_3, p.FromListConnector([(0, 0)]), struct_pl_stdp)
    proj_4 = p.Projection(
        stim, pop_4, p.FromListConnector([(0, 0)]), struct_pl_stdp)
    p.Projection(pop_3, pop_4, p.AllToAllConnector(),
                 p.StaticSynapse(weight=1, delay=3))
    p.run(10)

    conns = list(proj.get(["weight", "delay"], "list"))
    conns_2 = list(proj_2.get(["weight", "delay"], "list"))
    conns_3 = list(proj_3.get(["weight", "delay"], "list"))
    conns_4 = list(proj_4.get(["weight", "delay"], "list"))

    p.end()

    print(conns)
    print(conns_2)
    print(conns_3)
    print(conns_4)

    assert(len(conns) == 1)
    assert(tuple(conns[0]) == (0, 0, w_init, delay_init))
    assert(len(conns_2) == 1)
    assert(tuple(conns_2[0]) == (0, 0, w_init, delay_init))
    assert(len(conns_3) == 0)
    assert(len(conns_4) == 0)


class TestStructuralShared(BaseTestCase):

    def test_structural_shared(self):
        self.runsafe(structural_shared)


if __name__ == "__main__":
    structural_shared()

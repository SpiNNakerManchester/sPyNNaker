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

import numpy
import pyNN.spiNNaker as sim

from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel


class TestSTDPRandomRun(BaseTestCase):
    # Test that reset with STDP and using Random weights results in the
    # same thing being loaded twice, both with data generated off and on the
    # machine

    def run_model(self, model: AbstractPyNNModel) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp(i_offset=5.0), label="pop")
        pop.record("spikes")
        pop_2 = sim.Population(1, model, label="pop_2")
        proj = sim.Projection(
            pop, pop_2, sim.AllToAllConnector(),
            sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(),
                weight_dependence=sim.AdditiveWeightDependence(),
                weight=sim.RandomDistribution("uniform", low=0.3, high=0.7)))
        proj_2 = sim.Projection(
            pop, pop_2, sim.OneToOneConnector(),
            sim.STDPMechanism(
                timing_dependence=sim.SpikePairRule(),
                weight_dependence=sim.AdditiveWeightDependence(),
                weight=sim.RandomDistribution("uniform", low=0.3, high=0.7)))
        sim.run(100)
        weights_1_1 = proj.get("weight", "list")
        weights_1_2 = proj_2.get("weight", "list")
        spikes_1 = pop.get_data("spikes").segments[0].spiketrains

        sim.reset()
        sim.run(100)
        weights_2_1 = proj.get("weight", "list")
        weights_2_2 = proj_2.get("weight", "list")
        spikes_2 = pop.get_data("spikes").segments[1].spiketrains
        sim.end()

        assert numpy.array_equal(weights_1_1, weights_2_1)
        assert numpy.array_equal(weights_1_2, weights_2_2)
        assert len(spikes_1[0]) > 0
        assert numpy.array_equal(spikes_1, spikes_2)

    def _do_if_curr_exp(self) -> None:
        self.run_model(sim.IF_curr_exp())

    def test_check_if_curr_exp(self) -> None:
        self.runsafe(self._do_if_curr_exp)
        self.check_binary_used("IF_curr_exp_stdp_mad_pair_additive.aplx")

    def _do_if_curr_exp_ca2_additive(self) -> None:
        self.run_model(sim.extra_models.IFCurrExpCa2Adaptive())

    def test_check_if_curr_exp(self) -> None:
        self.runsafe(self._do_if_curr_exp_ca2_additive)
        self.check_binary_used(
            "IF_curr_exp_ca2_adaptive_stdp_mad_pair_additive.aplx")

    def _do_izk_cond_exp_dual(self) -> None:
        self.run_model(sim.extra_models.Izhikevich_cond_dual())

    def test_check_if_curr_exp(self) -> None:
        self.runsafe(self._do_izk_cond_exp_dual)
        self.check_binary_used(
            "IZK_cond_exp_dual_stdp_mad_pair_additive.aplx")

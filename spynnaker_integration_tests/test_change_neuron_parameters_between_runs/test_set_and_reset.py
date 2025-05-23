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

from numpy.typing import NDArray
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestNoChange(BaseTestCase):

    def check_from_65(self, v: NDArray) -> None:
        for i in range(0, len(v), 5):
            assert -65. == v[i+0][2]
            assert -64.024658203125 == v[i+1][2]
            assert -63.09686279296875 == v[i+2][2]
            assert -62.214324951171875 == v[i+3][2]
            assert -61.37481689453125 == v[i+4][2]

    def check_from_60(self, v: NDArray) -> None:
        assert -60. == v[0][2]
        assert -59.26849365234375 == v[1][2]
        assert -58.5726318359375 == v[2][2]
        assert -57.91070556640625 == v[3][2]
        assert -57.28106689453125 == v[4][2]

    def change_nothing(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        v1 = pop.spinnaker_get_data('v')
        self.check_from_65(v1)
        sim.reset()
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_65(v2)
        sim.end()

    def test_change_nothing(self) -> None:
        self.runsafe(self.change_nothing)

    def change_pre_reset(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        v1 = pop.spinnaker_get_data('v')
        self.check_from_65(v1)
        pop.set(tau_syn_E=1)
        sim.reset()
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        sim.end()
        self.check_from_65(v2)

    def test_change_pre_reset(self) -> None:
        self.runsafe(self.change_pre_reset)

    def run_set_run_reset(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(2)
        pop.set(tau_syn_E=1)
        sim.run(3)
        v1 = pop.spinnaker_get_data('v')
        self.check_from_65(v1)
        sim.reset()

        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_65(v2)
        sim.end()

    def test_run_set_run_reset(self) -> None:
        self.runsafe(self.run_set_run_reset)

    def run_set_run_reset_set(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(2)
        pop.set(tau_syn_E=1)
        sim.run(3)
        v1 = pop.spinnaker_get_data('v')
        self.check_from_65(v1)
        sim.reset()
        pop.set(tau_syn_E=1)
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        sim.end()
        self.check_from_65(v2)

    def test_run_set_run_reset_set(self) -> None:
        self.runsafe(self.run_set_run_reset_set)

    def change_post_set(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        v1 = pop.spinnaker_get_data('v')
        self.check_from_65(v1)
        sim.reset()
        pop.set(tau_syn_E=1)
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_65(v2)
        sim.end()

    def test_change_post_set(self) -> None:
        self.runsafe(self.change_post_set)

    def no_change_v(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        sim.reset()
        inp.set(spike_times=[100])
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_65(v2)
        sim.end()

    def test_no_change_v(self) -> None:
        self.runsafe(self.no_change_v)

    def change_v_before(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        sim.reset()
        pop.initialize(v=-65)
        inp.set(spike_times=[100])
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_65(v2)
        sim.end()

    def test_change_v_before(self) -> None:
        self.runsafe(self.change_v_before)

    def change_v_after(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.record(["v"])
        sim.run(5)
        sim.reset()
        pop.initialize(v=-65)
        inp.set(spike_times=[100])
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_65(v2)
        sim.end()

    def test_change_v_after(self) -> None:
        self.runsafe(self.change_v_after)

    def no_change_with_v_set(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.initialize(v=-60)
        pop.record(["v"])
        sim.run(5)
        sim.reset()
        inp.set(spike_times=[100])
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        self.check_from_60(v2)
        sim.end()

    def test_no_change_with_v_set(self) -> None:
        self.runsafe(self.no_change_with_v_set)

    def reset_set_with_v_set(self) -> None:
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        inp = sim.Population(1, sim.SpikeSourceArray(
            spike_times=[0]), label="input")
        sim.Projection(inp, pop, sim.OneToOneConnector(),
                       synapse_type=sim.StaticSynapse(weight=5))
        pop.set(i_offset=1.0)
        pop.set(tau_syn_E=1)
        pop.initialize(v=-60)
        pop.record(["v"])
        sim.run(5)
        pop.set(tau_syn_E=1)
        sim.reset()
        inp.set(spike_times=[100])
        sim.run(5)
        v2 = pop.spinnaker_get_data('v')
        sim.end()
        self.check_from_60(v2)

    def test_reset_set_with_v_set(self) -> None:
        self.runsafe(self.reset_set_with_v_set)

    def multi_core(self) -> None:
        sim.setup(1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 2)
        pop = sim.Population(
            6, sim.IF_curr_exp(i_offset=1, tau_syn_E=1), label="pop")
        pop.record("v")
        sim.run(3)
        pop.set(tau_syn_E=1)
        sim.run(2)
        v1 = pop.spinnaker_get_data('v')
        sim.end()
        self.check_from_65(v1)

    def test_multi_core(self) -> None:
        self.runsafe(self.multi_core)

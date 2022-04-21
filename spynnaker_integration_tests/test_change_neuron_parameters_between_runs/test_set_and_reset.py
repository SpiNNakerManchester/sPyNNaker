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

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase


class TestNoChange(BaseTestCase):

    def check_from_65(self, v):
        for i in range(0, len(v), 5):
            assert -65. == v[i+0][2]
            assert -64.024658203125 == v[i+1][2]
            assert -63.09686279296875 == v[i+2][2]
            assert -62.214324951171875 == v[i+3][2]
            assert -61.37481689453125 == v[i+4][2]

    def check_from_60(self, v):
        assert -60. == v[0][2]
        assert -59.26849365234375 == v[1][2]
        assert -58.5726318359375 == v[2][2]
        assert -57.91070556640625 == v[3][2]
        assert -57.28106689453125 == v[4][2]

    def change_nothing(self):
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

    def test_change_nothing(self):
        self.runsafe(self.change_nothing)

    def change_pre_reset(self):
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

    def test_change_pre_reset(self):
        self.runsafe(self.change_pre_reset)

    def run_set_run_reset(self):
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

    def test_run_set_run_reset(self):
        self.runsafe(self.run_set_run_reset)

    def run_set_run_reset_set(self):
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

    def test_run_set_run_reset_set(self):
        self.runsafe(self.run_set_run_reset_set)

    def change_post_set(self):
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

    def test_change_post_set(self):
        self.runsafe(self.change_post_set)

    def no_change_v(self):
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

    def test_no_change_v(self):
        self.runsafe(self.no_change_v)

    def change_v_before(self):
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

    def test_change_v_before(self):
        self.runsafe(self.change_v_before)

    def change_v_after(self):
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

    def test_change_v_after(self):
        self.runsafe(self.change_v_after)

    def no_change_with_v_set(self):
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

    def test_no_change_with_v_set(self):
        self.runsafe(self.no_change_with_v_set)

    def reset_set_with_v_set(self):
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

    def test_reset_set_with_v_set(self):
        self.runsafe(self.reset_set_with_v_set)

    def multi_core(self):
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

    def test_multi_core(self):
        self.runsafe(self.multi_core)

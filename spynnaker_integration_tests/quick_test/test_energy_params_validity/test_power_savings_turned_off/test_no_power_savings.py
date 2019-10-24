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

from testfixtures import LogCapture
import spynnaker as sim
from spynnaker_integration_tests.base_test_case import BaseTestCase


class Synfire2RunExtractionIfCurrExp(BaseTestCase):

    def do_run(self):
        with LogCapture() as lc:
            sim.setup(1.0)
            pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
            inp = sim.Population(1, sim.SpikeSourceArray(
                spike_times=[0]), label="input")
            sim.Projection(inp, pop, sim.OneToOneConnector(),
                           synapse_type=sim.StaticSynapse(weight=5))
            sim.run(10)
            self.assert_logs_messages(
                lc.records, "Working out if machine is booted", 'INFO', 1)

    def test_do_run(self):
        self.runsafe(self.do_run)

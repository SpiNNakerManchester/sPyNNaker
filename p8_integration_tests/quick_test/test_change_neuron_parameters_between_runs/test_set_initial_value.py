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

import spynnaker8 as p
from p8_integration_tests.base_test_case import BaseTestCase


class TestSetInitialValue(BaseTestCase):

    # pop.set_inital_value is not a standard PyNN call, but
    # we allow it on SpiNNaker, so we should test it (between runs)

    def set_initial_value_between_runs(self):
        runtime1 = 50
        runtime2 = 200

        p.setup(timestep=1.0)

        pop1 = p.Population(1, p.SpikeSourceArray([10, 100]))
        pop2 = p.Population(1, p.IF_curr_exp())

        p.Projection(pop1, pop2, p.AllToAllConnector(),
                     p.StaticSynapse(weight=1.0, delay=1.0))

        pop2[0].record(['v'])

        p.run(runtime1)
        pop2.set_initial_value(variable="v", value=-65)
        p.run(runtime2)

        v = pop2.get_data('v')

        p.end()

        assert v.segments[0].filter(name='v')[0][runtime1] == -65.0

    def test_set_initial_value_between_runs(self):
        self.runsafe(self.set_initial_value_between_runs)

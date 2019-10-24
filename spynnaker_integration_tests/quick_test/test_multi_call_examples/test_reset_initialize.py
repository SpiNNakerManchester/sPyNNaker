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

import spynnaker as sim
from spynnaker_integration_tests.base_test_case import BaseTestCase


class TestResetInitialize(BaseTestCase):
    # Test that resets and initialises, checking that membrane voltages
    # are reset and initialised correctly

    def do_run(self):
        sim.setup(1.0)
        pop = sim.Population(1, sim.IF_curr_exp, {}, label="pop")
        pop.set(i_offset=1.0)
        pop.record(["v"])
        initial1 = -64.0
        initial2 = -62.0
        initial3 = -63.0
        initial4 = -61.0
        runtime = 10

        pop.initialize(v=initial1)
        sim.run(runtime)

        sim.reset()
        pop.initialize(v=initial2)
        sim.run(runtime)

        sim.reset()
        pop.initialize(v=initial3)
        pop.set(i_offset=2.0)
        sim.run(runtime)

        try:
            pop.initialize(v=initial4)  # this should throw an exception
        except Exception:
            pass

        pop.set(i_offset=2.5)
        sim.run(runtime)

        v = pop.get_data('v')

        sim.end()

        # test values at start of each run() call above
        self.assertEqual(v.segments[0].filter(name='v')[0][0], initial1)
        self.assertEqual(v.segments[1].filter(name='v')[0][0], initial2)
        self.assertEqual(v.segments[2].filter(name='v')[0][0], initial3)
        self.assertNotEqual(v.segments[2].filter(name='v')[0][runtime],
                            initial4)

        # test the lengths of each segment are correct
        self.assertEqual(len(v.segments[0].filter(name='v')[0]), runtime)
        self.assertEqual(len(v.segments[0].filter(name='v')[0]),
                         len(v.segments[1].filter(name='v')[0]))
        self.assertEqual(len(v.segments[2].filter(name='v')[0]), 2 * runtime)

    def test_do_run(self):
        self.runsafe(self.do_run)

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

from p8_integration_tests.base_test_case import BaseTestCase
import p8_integration_tests.scripts.pynnBrunnelBrianNestSpinnaker as script

Neurons = 3000  # number of neurons in each population
sim_time = 1000
simulator_Name = 'spiNNaker'
record = False


class PynnBrunnelBrianNestSpinnaker(BaseTestCase):

    def test_run(self):
        self.assert_not_spin_three()
        (esp, s, N_E) = script.do_run(Neurons, sim_time, record=record)
        self.assertIsNone(esp)
        self.assertIsNone(s)
        self.assertEqual(2400, N_E)


if __name__ == '__main__':
    (esp, s, N_E) = script.do_run(Neurons, sim_time, record=record)
    print(esp)
    print(s)
    print(N_E)

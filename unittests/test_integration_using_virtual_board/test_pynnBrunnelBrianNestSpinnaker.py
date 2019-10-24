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

from spynnaker_integration_tests.base_test_case import BaseTestCase
import spynnaker_integration_tests.scripts.pynnBrunnelBrianNestSpinnaker as script

Neurons = 3000  # number of neurons in each population
sim_time = 1000
simulator_Name = 'spiNNaker'


class PynnBrunnelBrianNestSpinnaker(BaseTestCase):

    # AttributeError: 'SpikeSourcePoisson' object has no attribute 'describe'
    def test_run(self):
        script.do_run(Neurons, sim_time, record=True)


if __name__ == '__main__':
    x = PynnBrunnelBrianNestSpinnaker()
    x.test_run()

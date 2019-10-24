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
import spynnaker_integration_tests.scripts.synfire_npop_run as synfire_npop_run

n_neurons = 10  # number of neurons in each population
n_pops = 630


class Synfire6300n10pop10pc48chipsNoDelaysSpikeRecording(BaseTestCase):

    def test_run(self):
        synfire_npop_run.do_run(n_neurons, n_pops=n_pops,
                                neurons_per_core=n_neurons)


if __name__ == '__main__':
    x = Synfire6300n10pop10pc48chipsNoDelaysSpikeRecording()
    x.test_run()

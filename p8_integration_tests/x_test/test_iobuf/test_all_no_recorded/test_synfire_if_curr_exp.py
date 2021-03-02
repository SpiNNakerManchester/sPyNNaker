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

"""
Synfirechain-like example
"""
from spinnaker_testbase import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner

n_neurons = 200  # number of neurons in each population
runtime = 5000
neurons_per_core = n_neurons / 2
synfire_run = SynfireRunner()


class SynfireIfCurrExp(BaseTestCase):

    def test_run(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=[runtime], record=False, record_v=False,
                           record_gsyn_exc=False, record_gsyn_inh=False)


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=[runtime], record=False, record_v=False,
                       record_gsyn_exc=False, record_gsyn_inh=False)

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
import spynnaker.plot_utils as plot_utils
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner

n_neurons = 200  # number of neurons in each population
runtime = 5000
neurons_per_core = n_neurons / 2
record = False
record_v = True
record_gsyn = False
synfire_run = SynfireRunner()


class SynfireIfCurrExp(BaseTestCase):

    def test_run(self):
        synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                           run_times=[runtime], record=record,
                           record_v=record_v, record_gsyn_exc=record_gsyn)
        gsyn = synfire_run.get_output_pop_gsyn_exc_list()
        v = synfire_run.get_output_pop_voltage_list()
        spikes = synfire_run.get_output_pop_spikes_list()

        self.assertEqual(1, len(v))
        self.assertEqual(0, len(gsyn))
        self.assertEqual(0, len(spikes))


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, neurons_per_core=neurons_per_core,
                       run_times=[runtime], record=record, record_v=record_v,
                       record_gsyn_exc=record_gsyn)
    _gsyn = synfire_run.get_output_pop_gsyn_exc_list()
    _v = synfire_run.get_output_pop_voltage_numpy()
    _spikes = synfire_run.get_output_pop_spikes_list()

    plot_utils.line_plot(_v, title="v")

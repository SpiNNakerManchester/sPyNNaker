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

# spynnaker imports
import os
from neo.io import PickleIO
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner
import spynnaker.plot_utils as plot_utils
import spynnaker.spike_checker as spike_checker
import spynnaker.gsyn_tools as gsyn_tools
from spynnaker8.utilities import neo_compare


n_neurons = 10  # number of neurons in each population
max_delay = 14.4
timestep = 1
neurons_per_core = n_neurons/2
delay = 1.7
runtime = 50
gsyn_path = os.path.dirname(os.path.abspath(__file__))
gsyn_path = os.path.join(gsyn_path, "gsyn.pickle")
synfire_run = SynfireRunner()


class TestPrintGsyn(BaseTestCase):
    """
    tests the printing of get gsyn given a simulation
    """

    def test_get_gsyn(self):
        synfire_run.do_run(n_neurons, max_delay=max_delay, time_step=timestep,
                           neurons_per_core=neurons_per_core, delay=delay,
                           run_times=[runtime], gsyn_path_exc=gsyn_path)
        spikes = synfire_run.get_output_pop_spikes_numpy()
        gsyn = synfire_run.get_output_pop_gsyn_exc_neo()

        self.assertEqual(12, len(spikes))
        spike_checker.synfire_spike_checker(spikes, n_neurons)
        io = PickleIO(filename=gsyn_path)
        gsyn_saved = io.read()[0]
        neo_compare.compare_blocks(gsyn, gsyn_saved)
        os.remove(gsyn_path)


if __name__ == '__main__':
    synfire_run.do_run(n_neurons, max_delay=max_delay, time_step=timestep,
                       neurons_per_core=neurons_per_core, delay=delay,
                       run_times=[runtime], gsyn_path_exc=gsyn_path)
    gsyn = synfire_run.get_output_pop_gsyn_exc_numpy()
    v = synfire_run.get_output_pop_voltage_numpy()
    spikes = synfire_run.get_output_pop_spikes_numpy()
    print(len(spikes))
    plot_utils.plot_spikes(spikes)
    plot_utils.heat_plot(v)
    plot_utils.heat_plot(gsyn)
    gsyn_tools.check_sister_gysn(__file__, n_neurons, runtime, gsyn)
    # os.remove(gsyn_path)

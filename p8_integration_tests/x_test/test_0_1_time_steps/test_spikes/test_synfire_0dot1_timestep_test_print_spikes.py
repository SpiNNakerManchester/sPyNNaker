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
import os
from neo.io import PickleIO
import unittest
from unittest import SkipTest
from spinnman.exceptions import SpinnmanTimeoutException
from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner
from spynnaker8.utilities import neo_compare

n_neurons = 20
timestep = 0.1
max_delay = 14.40
delay = 1.7
neurons_per_core = n_neurons/2
runtime = 500
current_file_path = os.path.dirname(os.path.abspath(__file__))
spike_path = os.path.join(current_file_path, "spikes.pickle")
synfire_run = SynfireRunner()


class TestPrintSpikes(BaseTestCase):
    """
    tests the printing of get spikes given a simulation
    """

    def test_print_spikes(self):
        try:
            synfire_run.do_run(n_neurons, time_step=timestep,
                               max_delay=max_delay, delay=delay,
                               neurons_per_core=neurons_per_core,
                               run_times=[runtime],
                               spike_path=spike_path)
            spikes = synfire_run.get_output_pop_spikes_neo()

            try:
                io = PickleIO(filename=spike_path)
                read_in_spikes = io.read()[0]

                neo_compare.compare_blocks(spikes, read_in_spikes)
            except UnicodeDecodeError as ex:
                raise SkipTest(
                    "https://github.com/NeuralEnsemble/python-neo/issues/529"
                    ) from ex

        except SpinnmanTimeoutException as ex:
            # System intentional overload so may error
            raise SkipTest() from ex


if __name__ == '__main__':
    unittest.main()

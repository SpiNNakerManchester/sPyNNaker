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
import unittest
from neo.io import PickleIO

from p8_integration_tests.base_test_case import BaseTestCase
from p8_integration_tests.scripts.synfire_run import SynfireRunner
from spynnaker8.utilities import neo_compare
from spinnman.exceptions import SpinnmanTimeoutException
from unittest import SkipTest

synfire_run = SynfireRunner()


class TestMallocKeyAllocatorWithSynfire(BaseTestCase):
    """
    tests the printing of print v given a simulation
    """

    def test_script(self):
        """
        test that tests the printing of v from a pre determined recording
        :return:
        """
        try:
            n_neurons = 20  # number of neurons in each population
            current_file_path = os.path.dirname(os.path.abspath(__file__))
            current_spike_file_path = os.path.join(current_file_path,
                                                   "spikes.pickle")
            current_v_file_path = os.path.join(current_file_path, "v.pickle")
            current_gsyn_file_path = os.path.join(current_file_path,
                                                  "gsyn.pickle")
            synfire_run.do_run(n_neurons, max_delay=14, time_step=0.1,
                               neurons_per_core=1, delay=1.7, run_times=[50],
                               spike_path=current_spike_file_path,
                               gsyn_path_exc=current_gsyn_file_path,
                               v_path=current_v_file_path)

            spikes_read = synfire_run.get_output_pop_spikes_neo()
            v_read = synfire_run.get_output_pop_voltage_neo()
            gsyn_read = synfire_run.get_output_pop_gsyn_exc_neo()

            io = PickleIO(filename=current_spike_file_path)
            spikes_saved = io.read()[0]
            io = PickleIO(filename=current_v_file_path)
            v_saved = io.read()[0]
            io = PickleIO(filename=current_gsyn_file_path)
            gsyn_saved = io.read()[0]

            neo_compare.compare_blocks(spikes_read, spikes_saved)
            neo_compare.compare_blocks(v_read, v_saved)
            neo_compare.compare_blocks(gsyn_read, gsyn_saved)

        except SpinnmanTimeoutException as ex:
            # System sometimes times outs
            raise SkipTest(ex)


if __name__ == '__main__':
    unittest.main()

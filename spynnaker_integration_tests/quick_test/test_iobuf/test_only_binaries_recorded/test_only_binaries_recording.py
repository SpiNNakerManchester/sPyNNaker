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
from unittest import SkipTest
import spynnaker as sim
from spynnaker_integration_tests.base_test_case import BaseTestCase


class TestCoresAndBinariesRecording(BaseTestCase):

    def do_run(self):
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=18))
        sim.run(500)

        provenance_files = self.get_provenance_files()
        sim.end()

        # assuming placements as expected
        xmls = {  # extract_iobuf_from_binary_types = IF_curr_exp.aplx
                "0_0_5_pop_1_0_99.xml", "0_0_6_pop_1_100_199.xml",
                }
        if xmls < set(provenance_files):
            # extract_iobuf_from_cores = None
            self.assertNotIn(
                "iobuf_for_chip_0_0_processor_id_2.txt", provenance_files)
            self.assertNotIn(
                "iobuf_for_chip_0_0_processor_id_3.txt", provenance_files)
            self.assertNotIn(
                "iobuf_for_chip_0_0_processor_id_4.txt", provenance_files)
            self.assertIn(
                "iobuf_for_chip_0_0_processor_id_5.txt", provenance_files)
            self.assertIn(
                "iobuf_for_chip_0_0_processor_id_6.txt", provenance_files)
        else:
            raise SkipTest("Unexpected placements {}".format(provenance_files))

    def test_do_run(self):
        self.runsafe(self.do_run)

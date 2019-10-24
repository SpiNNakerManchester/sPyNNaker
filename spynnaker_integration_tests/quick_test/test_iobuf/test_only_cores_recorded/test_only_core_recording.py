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
from spinn_front_end_common.utilities import globals_variables


class TestOnlyCoresRecording(BaseTestCase):

    def check_for_expected_iobuf(self, provenance_files, placements, x, y, p):
        if placements.is_processor_occupied(x, y, p):
            self.assertIn("iobuf_for_chip_{}_{}_processor_id_{}.txt".format(
                x, y, p), provenance_files)

    def do_run(self):
        # From the config file
        requested_cores = [(0, 0, 1), (0, 0, 3), (1, 1, 1)]
        sim.setup(timestep=1.0)
        sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

        input = sim.Population(1, sim.SpikeSourceArray(spike_times=[0]),
                               label="input")
        pop_1 = sim.Population(200, sim.IF_curr_exp(), label="pop_1")
        sim.Projection(input, pop_1, sim.AllToAllConnector(),
                       synapse_type=sim.StaticSynapse(weight=5, delay=18))
        sim.run(500)

        provenance_files = self.get_provenance_files()
        placements = globals_variables.get_simulator().placements
        sim.end()

        for placement in placements.placements:
            x, y, p = placement.x, placement.y, placement.p
            if (x, y, p) in requested_cores:
                self.check_for_expected_iobuf(
                    provenance_files, placements, x, y, p)
            else:
                self.assertNotIn(
                    "iobuf_for_chip_{}_{}_processor_id_{}.txt".format(
                        x, y, p), provenance_files)

    def test_do_run(self):
        self.runsafe(self.do_run)

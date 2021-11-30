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

import os
from spinn_front_end_common.utilities import globals_variables
import spynnaker8 as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView

class TestIobuffMultirun(BaseTestCase):

    def check_size(self, prov_path, placement):
        iofile = os.path.join(
            prov_path,
            "iobuf_for_chip_{}_{}_processor_id_{}.txt".format(
                placement.x, placement.y, placement.p))
        return os.path.getsize(iofile)

    def do_run(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        prov_path = SpynnakerDataView().app_provenance_dir_path
        pop = sim.Population(10, sim.IF_curr_exp(), label='pop_1')
        sim.run(50)

        placements = globals_variables.get_simulator()._placements
        machine_verts = list(pop._vertex.machine_vertices)
        placement = placements.get_placement_of_vertex(machine_verts[0])

        size1 = self.check_size(prov_path, placement)
        sim.run(50)
        size2 = self.check_size(prov_path, placement)
        self.assertGreater(size2, size1)
        sim.run(50)
        size3 = self.check_size(prov_path, placement)
        self.assertGreater(size3, size2)

        # Soft reset so same provenance
        sim.reset()
        sim.run(50)
        size4 = self.check_size(prov_path, placement)
        self.assertGreater(size4, size3)
        sim.run(50)
        size5 = self.check_size(prov_path, placement)
        self.assertGreater(size5, size4)

        # hard reset so new provenance
        sim.reset()
        sim.Population(10, sim.IF_curr_exp(), label='pop_1')
        sim.run(50)
        prov_patha = SpynnakerDataView().app_provenance_dir_path
        self.assertNotEqual(prov_path, prov_patha)
        size6 = self.check_size(prov_patha, placement)
        # Should write the same thing again
        self.assertEqual(size1, size6)
        sim.end()

        # Should not add anything on end.
        size7 = self.check_size(prov_path, placement)
        self.assertEqual(size5, size7)
        size8 = self.check_size(prov_patha, placement)
        self.assertEqual(size8, size6)

    def test_do_run(self):
        self.runsafe(self.do_run)

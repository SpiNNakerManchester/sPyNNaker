# Copyright (c) 2017-2022 The University of Manchester
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
import pyNN.spiNNaker as sim
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
        prov_path1 = SpynnakerDataView.get_app_provenance_dir_path()
        pop = sim.Population(10, sim.IF_curr_exp(), label='pop_1')
        sim.run(50)

        machine_verts = list(pop._vertex.machine_vertices)
        placement = SpynnakerDataView.get_placement_of_vertex(machine_verts[0])

        size1 = self.check_size(prov_path1, placement)
        sim.run(50)
        prov_path2 = SpynnakerDataView.get_app_provenance_dir_path()
        self.assertEqual(prov_path2, prov_path1)
        size2 = self.check_size(prov_path2, placement)
        self.assertGreater(size2, size1)
        sim.run(50)
        prov_path3 = SpynnakerDataView.get_app_provenance_dir_path()
        self.assertEqual(prov_path3, prov_path1)
        size3 = self.check_size(prov_path3, placement)
        self.assertGreater(size3, size2)

        # Soft reset new provenance but not full reset
        sim.reset()
        sim.run(50)
        prov_path4 = SpynnakerDataView.get_app_provenance_dir_path()
        self.assertNotEqual(prov_path4, prov_path1)
        size4 = self.check_size(prov_path4, placement)
        # Less as startup after soft reset different than original
        self.assertLess(size4, size1)
        sim.run(50)
        prov_path5 = SpynnakerDataView.get_app_provenance_dir_path()
        self.assertEqual(prov_path4, prov_path5)
        size5 = self.check_size(prov_path5, placement)
        self.assertGreater(size5, size4)

        # hard reset so new provenance
        sim.reset()
        sim.Population(10, sim.IF_curr_exp(), label='pop_1')
        sim.run(50)
        prov_path6 = SpynnakerDataView.get_app_provenance_dir_path()
        self.assertNotEqual(prov_path6, prov_path1)
        self.assertNotEqual(prov_path6, prov_path4)
        machine_verts = list(pop._vertex.machine_vertices)
        placement = SpynnakerDataView.get_placement_of_vertex(machine_verts[0])
        size6 = self.check_size(prov_path6, placement)
        # Should write the same thing as original again
        self.assertEqual(size1, size6)
        sim.end()

        # Should not add anything on end.
        # Before reset
        size3a = self.check_size(prov_path3, placement)
        self.assertEqual(size3, size3a)
        # Soft reset
        size5a = self.check_size(prov_path5, placement)
        self.assertEqual(size5a, size5)
        # Hard reset
        size6a = self.check_size(prov_path6, placement)
        self.assertEqual(size6a, size6)

    def test_do_run(self):
        self.runsafe(self.do_run)

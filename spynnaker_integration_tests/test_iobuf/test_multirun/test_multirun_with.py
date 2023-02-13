# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        prov_path = SpynnakerDataView.get_app_provenance_dir_path()
        pop = sim.Population(10, sim.IF_curr_exp(), label='pop_1')
        sim.run(50)

        machine_verts = list(pop._vertex.machine_vertices)
        placement = SpynnakerDataView.get_placement_of_vertex(machine_verts[0])

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
        prov_patha = SpynnakerDataView.get_app_provenance_dir_path()
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

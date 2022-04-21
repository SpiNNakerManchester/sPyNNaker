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
import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.data import SpynnakerDataView


class TestNoIobufDuringRun(BaseTestCase):

    def check_for_iobufs(self, prov_path):
        return any("iobuf" in filename and ".txt" in filename
                   for filename in os.listdir(prov_path))

    def do_run(self):
        sim.setup(timestep=1.0, min_delay=1.0)
        sim.Population(10, sim.IF_curr_exp(), label='pop_1')
        sim.run(500)
        prov_path = SpynnakerDataView.get_app_provenance_dir_path()

        self.assertFalse(self.check_for_iobufs(prov_path))
        sim.end()
        self.assertFalse(self.check_for_iobufs(prov_path))

    def test_do_run(self):
        self.runsafe(self.do_run)


if __name__ == '__main__':
    x = TestNoIobufDuringRun()
    x.do_run()

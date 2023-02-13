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

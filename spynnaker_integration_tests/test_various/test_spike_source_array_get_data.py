# Copyright (c) 2017 The University of Manchester
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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


class TestSpikeSourceArrayGetData(BaseTestCase):

    def do_run(self):
        p.setup(timestep=1, min_delay=1)

        population = p.Population(1, p.SpikeSourceArray(spike_times=[[0]]),
                                  label='inputSSA_1')

        population.record("all")

        p.run(30)
        population.get_data("all")
        p.end()

    def test_run(self):
        self.runsafe(self.do_run)

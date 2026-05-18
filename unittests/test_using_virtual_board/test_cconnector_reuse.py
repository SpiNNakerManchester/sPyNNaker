# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyNN.spiNNaker as sim
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN import SpynnakerException


class TestConnectorReuse(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_connector_reuse(self) -> None:
        sim.setup()
        connector = sim.OneToOneConnector()
        pop_1 = sim.Population(1, sim.IF_curr_exp(), label="pop_1")
        pop_2 = sim.Population(1, sim.IF_curr_exp(), label="pop_2")
        pop_3 = sim.Population(1, sim.IF_curr_exp(), label="pop_2")
        sim.Projection(pop_1, pop_2, connector)
        with self.assertRaises(SpynnakerException):
            sim.Projection(pop_1, pop_3, connector)
        sim.end()

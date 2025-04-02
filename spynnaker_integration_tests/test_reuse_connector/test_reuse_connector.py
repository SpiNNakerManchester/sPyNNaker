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

from typing import Tuple
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase
from spynnaker.pyNN.models.neuron import ConnectionHolder


def do_run() -> Tuple[ConnectionHolder, ConnectionHolder]:

    p.setup(timestep=1.0)
    inp = p.Population(1, p.SpikeSourceArray(spike_times=[0]))
    out = p.Population(1, p.IF_curr_exp())

    connector = p.OneToOneConnector()

    proj_1 = p.Projection(inp, out, connector,
                          p.StaticSynapse(weight=2.0, delay=2.0))
    proj_2 = p.Projection(inp, out, connector,
                          p.StaticSynapse(weight=1.0, delay=1.0))

    p.run(1)

    proj_1_list = proj_1.get(("weight", "delay"), "list")
    proj_2_list = proj_2.get(("weight", "delay"), "list")
    p.end()

    return proj_1_list, proj_2_list


class ReuseConnectorTest(BaseTestCase):
    def check_run(self) -> None:
        proj_1_list, proj_2_list = do_run()
        # any checks go here
        test_1_list = []
        test_1_list.append((0, 0, 2.0, 2.0))
        test_2_list = []
        test_2_list.append((0, 0, 1.0, 1.0))
        self.assertEqual(1, len(proj_1_list))
        self.assertEqual(1, len(proj_2_list))
        for i in range(4):
            test_1 = test_1_list[0]
            assert isinstance(test_1, list)
            proj_1 = proj_1_list[0]
            assert isinstance(proj_1, list)
            self.assertEqual(test_1[i], proj_1[i])
            test_2 = test_2_list[0]
            assert isinstance(test_2, list)
            proj_2 = proj_2_list[0]
            assert isinstance(proj_2, list)
            self.assertEqual(test_2[i], proj_2[i])

    def test_run(self) -> None:
        self.runsafe(self.check_run)


if __name__ == '__main__':
    proj_1_list, proj_2_list = do_run()

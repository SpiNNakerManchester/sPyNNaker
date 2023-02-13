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

import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run():

    p.setup(timestep=1.0)
    # The larger population needs to be first for this test
    inp1 = p.Population(10, p.SpikeSourceArray(spike_times=[0]))
    out1 = p.Population(10, p.IF_curr_exp())
    inp2 = p.Population(5, p.SpikeSourceArray(spike_times=[0]))
    out2 = p.Population(5, p.IF_curr_exp())

    # Using an AllToAll to avoid the OneToOne's direct matrix
    connector = p.AllToAllConnector()

    proj_1 = p.Projection(inp1, out1, connector,
                          p.StaticSynapse(weight=2.0, delay=4.0))
    proj_2 = p.Projection(inp2, out2, connector,
                          p.StaticSynapse(weight=1.0, delay=3.0))

    p.run(1)

    proj_1_list = proj_1.get(("weight", "delay"), "list")
    proj_2_list = proj_2.get(("weight", "delay"), "list")
    p.end()

    return proj_1_list, proj_2_list


class ReuseConnectorDifferentPopsTest(BaseTestCase):
    def check_run(self):
        proj_1_list, proj_2_list = do_run()
        # Check the lists are the correct length and
        # have the correct weights / delays
        self.assertEqual(100, len(proj_1_list))
        self.assertEqual(25, len(proj_2_list))
        self.assertEqual(2.0, proj_1_list[0][2])
        self.assertEqual(4.0, proj_1_list[0][3])
        self.assertEqual(1.0, proj_2_list[0][2])
        self.assertEqual(3.0, proj_2_list[0][3])

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    proj_1_list, proj_2_list = do_run()
    print(len(proj_1_list), proj_1_list)
    print(len(proj_2_list), proj_2_list)

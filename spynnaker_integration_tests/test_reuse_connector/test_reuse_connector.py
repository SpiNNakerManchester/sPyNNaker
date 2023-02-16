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


def do_run():

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
    def check_run(self):
        proj_1_list, proj_2_list = do_run()
        # any checks go here
        test_1_list = []
        test_1_list.append((0, 0, 2.0, 2.0))
        test_2_list = []
        test_2_list.append((0, 0, 1.0, 1.0))
        self.assertEqual(1, len(proj_1_list))
        self.assertEqual(1, len(proj_2_list))
        for i in range(4):
            self.assertEqual(test_1_list[0][i], proj_1_list[0][i])
            self.assertEqual(test_2_list[0][i], proj_2_list[0][i])

    def test_run(self):
        self.runsafe(self.check_run)


if __name__ == '__main__':
    proj_1_list, proj_2_list = do_run()

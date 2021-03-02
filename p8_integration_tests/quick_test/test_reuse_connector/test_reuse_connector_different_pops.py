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

import spynnaker8 as p
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

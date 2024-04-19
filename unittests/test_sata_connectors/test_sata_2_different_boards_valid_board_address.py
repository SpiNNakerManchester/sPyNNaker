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

"""
retina example that just feeds data from a retina to live output via an
intermediate population
"""
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run():
    # Setup
    p.setup(timestep=1.0, n_boards_required=3)

    src_1 = p.Population(
        None,
        p.external_devices.ArbitraryFPGADevice(
            2000, fpga_link_id=12, fpga_id=1,
            board_address="127.0.0.0",
            label="src_1")
        )

    src_2 = p.Population(
        None,
        p.external_devices.ArbitraryFPGADevice(
            2000, fpga_link_id=11, fpga_id=1,
            board_address="127.0.4.8",
            label="src_2")
        )

    tgt = p.Population(1, p.IF_curr_exp(), label="tgt")
    p.Projection(src_1, tgt, p.AllToAllConnector())
    p.Projection(src_2, tgt, p.AllToAllConnector())

    p.run(1000)
    p.end()


class Sata2DifferentBoardsValidBoardAddress(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_sata_2_different_boards_valid_board_address(self):
        do_run()


if __name__ == '__main__':
    do_run()

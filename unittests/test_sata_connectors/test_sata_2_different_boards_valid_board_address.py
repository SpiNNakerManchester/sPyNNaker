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
retina example that just feeds data from a retina to live output via an
intermediate population
"""
import pyNN.spiNNaker as p
from spinnaker_testbase import BaseTestCase


def do_run():
    # Setup
    p.setup(timestep=1.0)

    p.Population(
        None,
        p.external_devices.ArbitraryFPGADevice(
            2000, fpga_link_id=12, fpga_id=1,
            board_address="127.0.0.0",
            label="bacon")
        )

    p.Population(
        None,
        p.external_devices.ArbitraryFPGADevice(
            2000, fpga_link_id=11, fpga_id=1,
            board_address="127.0.4.8",
            label="bacon")
        )

    p.run(1000)
    p.end()


class Sata2DifferentBoardsValidBoardAddress(BaseTestCase):

    # NO unittest_setup() as sim.setup is called

    def test_sata_2_different_boards_valid_board_address(self):
        do_run()


if __name__ == '__main__':
    do_run()

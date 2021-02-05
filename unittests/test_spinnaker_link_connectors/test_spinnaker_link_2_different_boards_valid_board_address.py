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
import spynnaker8 as p
from p8_integration_tests.base_test_case import BaseTestCase


def do_run():
    # Setup
    p.setup(timestep=1.0)

    # FPGA Retina
    retina_device = p.external_devices.ExternalFPGARetinaDevice

    p.Population(
        16384, retina_device,
        {'spinnaker_link_id': 0, 'board_address': "127.0.0.0",
         'retina_key': 0x5,
         'mode': retina_device.MODE_128,
         'polarity': retina_device.DOWN_POLARITY},
        label='External spinnaker link')

    p.Population(
        16384, retina_device,
        {'spinnaker_link_id': 0, 'board_address': "127.0.4.8",
         'retina_key': 0x5,
         'mode': retina_device.MODE_128,
         'polarity': retina_device.DOWN_POLARITY},
        label='External spinnaker link 2')

    p.run(1000)
    p.end()


class SpinnakerLink2DifferentBoardsValidBoardAddressTest(BaseTestCase):

    def test_spinnaker_link_2_different_boards_valid_board_address(self):
        do_run()


if __name__ == "__main__":
    do_run()

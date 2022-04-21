# Copyright (c) 2017-2022 The University of Manchester
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

from unittest import SkipTest
from spinn_utilities.config_holder import set_config
from spinnman.processes.get_machine_process import GetMachineProcess
from spinnaker_testbase import BaseTestCase
import pyNN.spiNNaker as sim


def hacked_receive_chip_info(self, scp_read_chip_info_response):
    chip_info = scp_read_chip_info_response.chip_info
    self._chip_info[chip_info.x, chip_info.y] = chip_info

    # Hack to test ignores
    if (chip_info.x == 8 and chip_info.y == 4):
        # hack the config to include an actual ip address used
        set_config("Machine", "down_cores",
                   f"3,0,-4:99,99,2:2,2,-19:3,3,4,127.0.0.1:"
                   f"2,2,-10,{chip_info.ethernet_ip_address}:"
                   f"2,2,-9,{chip_info.ethernet_ip_address}:"
                   f"2,2,4,{chip_info.ethernet_ip_address}")
        set_config("Machine", "down_chips",
                   f"6,7:3,3,127.0.0.1:"
                   f"3,3,{chip_info.ethernet_ip_address}")
        set_config("Machine", "down_links",
                   f"3,3,4,127.0.0.1:5,5,2:"
                   f"4,4,1,{chip_info.ethernet_ip_address}")


class TestAllow(BaseTestCase):

    def test_with_actual_ip_address(self):
        sim.setup(timestep=1.0, n_boards_required=6)
        self.assert_not_spin_three()

        # Hack in to set the ignores with used ipaddress
        GetMachineProcess._receive_chip_info = hacked_receive_chip_info

        machine = sim.get_machine()
        sim.end()

        # global 3,3 should exists
        three_zero = machine.get_chip_at(3, 0)
        if three_zero is None:
            raise SkipTest("Unexpected but not impossible missing chip")

        three_three = machine.get_chip_at(3, 3)
        if three_three is None:
            raise SkipTest("Unexpected but not impossible missing chip")

        ten_six = machine.get_chip_at(10, 6)
        if ten_six is None:
            raise SkipTest("Unexpected but not impossible missing chip")

        # self._ignore_chips.add((3, 3, chip_info.ethernet_ip_address))
        self.assertFalse(machine.is_chip_at(11, 7))

        # self._ignore_links.add((4, 4, 1, chip_info.ethernet_ip_address))
        self.assertFalse(machine.is_link_at(12, 8, 1))

        # self._ignore_cores.add((2, 2, -10, chip_info.ethernet_ip_address))
        # physical 10 is nearly always the monitor so skip discarded
        self.assertTrue(ten_six.is_processor_with_id(0))

        # self._ignore_cores.add((2, 2, 4, chip_info.ethernet_ip_address))
        self.assertFalse(ten_six.is_processor_with_id(4))

        # self._ignore_cores.add((2, 2, -9, chip_info.ethernet_ip_address))
        if ten_six.is_processor_with_id(10):
            raise SkipTest("Physical core 9 nearly always maps to virtual 10")

        # down_cores = 3,0,-4
        if three_zero.is_processor_with_id(5):
            raise SkipTest("Physical core 4 nearly always maps to virtual 5")

        # down_chips = 6,7
        self.assertFalse(machine.is_chip_at(6, 7))

        # down_links = 5,5,2
        self.assertFalse(machine.is_link_at(5, 5, 2))

        # down_cores = 3,3,4,127.0.0.1
        self.assertTrue(three_three.is_processor_with_id(4))

        # down_links = 3,3,4,127.0.0.1
        if not machine.is_link_at(3, 3, 4):
            raise SkipTest("Link 3 3 4 missing could be random hardware")


if __name__ == '__main__':
    # Hack in to set the ignores with used ipaddress
    GetMachineProcess._receive_chip_info = hacked_receive_chip_info

    sim.setup(timestep=1.0, n_boards_required=6)
    machine = sim.get_machine()
    sim.end()

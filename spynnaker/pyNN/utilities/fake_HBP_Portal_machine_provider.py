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

from spynnaker.pyNN.exceptions import InvalidParameterType


class FakeHBPPortalMachineProvider(object):
    __slots__ = ["__height", "__ip_addresses", "__width"]

    def __init__(self, n_boards, config):
        self.__ip_addresses = config.get("Machine", "machineName")
        self.__width = 8
        self.__height = 8
        if n_boards != 1:
            raise InvalidParameterType("Not enough machine size")

    def create(self):
        return

    def wait_until_ready(self):
        return

    def get_machine_info(self):
        connections = {"(0, 0)": self.__ip_addresses}
        return {'connections': connections,
                'width': self.__width,
                'height': self.__height,
                'machine_name': "BOB"}

    def destroy(self):
        print("PORTAL DESTROYED!")

    def wait_till_not_ready(self):
        while True:
            pass

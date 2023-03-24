# Copyright (c) 2016 The University of Manchester
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

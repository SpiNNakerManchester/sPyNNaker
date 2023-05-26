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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractEthernetTranslator(object, metaclass=AbstractBase):
    """
    A module that can translate packets received over Ethernet into
    control of an external device.
    """

    __slots__ = ()

    @abstractmethod
    def translate_control_packet(self, multicast_packet):
        """
        Translate a multicast packet received over Ethernet and send
        appropriate messages to the external device.

        :param multicast_packet: A received multicast packet
        :type multicast_packet:
            ~spinnman.messages.eieio.data_messages.AbstractDataElement
        """

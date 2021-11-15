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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractEthernetTranslator(object, metaclass=AbstractBase):
    """ A module that can translate packets received over Ethernet into\
        control of an external device
    """

    __slots__ = []

    @abstractmethod
    def translate_control_packet(self, multicast_packet):
        """ Translate a multicast packet received over Ethernet and send\
            appropriate messages to the external device.

        :param multicast_packet: A received multicast packet
        :type multicast_packet:
            ~spinnman.messages.eieio.data_messages.AbstractEIEIODataElement
        :rtype: None
        """

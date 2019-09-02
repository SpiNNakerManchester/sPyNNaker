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

import logging
from spinn_front_end_common.utility_models import MultiCastCommand
from spinnman.messages.eieio.data_messages import (
    EIEIODataMessage, KeyDataElement, KeyPayloadDataElement)
from spinn_front_end_common.utilities.connections import LiveEventConnection

logger = logging.getLogger(__name__)


class EthernetControlConnection(LiveEventConnection):
    """ A connection that can translate Ethernet control messages received\
        from a Population
    """
    __slots__ = ["__translator"]

    def __init__(
            self, translator, label, live_packet_gather_label, local_host=None,
            local_port=None):
        """
        :param translator: The translator of multicast to control commands
        :param local_host: The optional host to listen on
        :param local_port: The optional port to listen on
        """
        super(EthernetControlConnection, self).__init__(
            live_packet_gather_label, receive_labels=[label],
            local_host=local_host, local_port=local_port)
        self.__translator = translator

    def _receive_packet_callback(self, packet):
        if isinstance(packet, EIEIODataMessage):
            while packet.is_next_element:
                self._translate(packet.next_element)

    def _translate(self, element):
        if isinstance(element, KeyDataElement):
            self.__translator.translate_control_packet(
                MultiCastCommand(element.key))
        elif isinstance(element, KeyPayloadDataElement):
            self.__translator.translate_control_packet(
                MultiCastCommand(element.key, element.payload))

    def close(self):
        """ Close the connection
        """
        self.__running = False
        self.__receiver.close()
        super(EthernetControlConnection, self).close()

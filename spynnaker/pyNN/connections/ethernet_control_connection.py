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
from threading import Thread
from spinn_front_end_common.utility_models import MultiCastCommand
from spinnman.connections.udp_packet_connections import EIEIOConnection
from spinnman.messages.eieio.data_messages import (
    EIEIODataMessage, KeyDataElement, KeyPayloadDataElement)

logger = logging.getLogger(__name__)


class EthernetControlConnection(EIEIOConnection):
    """ A connection that can translate Ethernet control messages received\
        from a Population
    """
    # __slots__ = []  # FIXME: Sort out messy class hierarchy

    def __init__(
            self, translator, local_host=None, local_port=None):
        """
        :param translator: The translator of multicast to control commands
        :param local_host: The optional host to listen on
        :param local_port: The optional port to listen on
        """
        super(EthernetControlConnection, self).__init__(
            local_host=local_host, local_port=local_port)
        thread = Thread(name="Ethernet Control Connection on {}:{}".format(
            self.local_ip_address, self.local_port), target=self.run)
        thread.daemon = True
        self.__translator = translator
        self.__running = True
        thread.start()

    def run(self):
        try:
            while self.__running:
                self._step()
        except Exception:
            if self.__running:
                logger.exception("failure processing EIEIO message")

    def _step(self):
        message = self.receive_eieio_message()
        if isinstance(message, EIEIODataMessage):
            while message.is_next_element:
                self._translate(message.next_element)

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
        super(EthernetControlConnection, self).close()

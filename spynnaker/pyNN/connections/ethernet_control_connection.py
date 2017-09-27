from spinn_front_end_common.utility_models import MultiCastCommand

from spinnman.connections.udp_packet_connections import EIEIOConnection
from spinnman.messages.eieio.data_messages \
    import EIEIODataMessage, KeyDataElement, KeyPayloadDataElement

import logging
from threading import Thread

logger = logging.getLogger(__name__)


class EthernetControlConnection(EIEIOConnection, Thread):
    """ A connection that can translate Ethernet control messages received\
        from a Population
    """

    def __init__(
            self, translator, local_host=None, local_port=None):
        """

        :param translator: The translator of multicast to control commands
        :param local_host: The optional host to listen on
        :param local_port: The optional port to listen on
        """
        EIEIOConnection.__init__(
            self, local_host=local_host, local_port=local_port)
        Thread.__init__(
            self, name="Ethernet Control Connection on {}:{}".format(
                self.local_ip_address, self.local_port))
        self._translator = translator
        self._running = True
        self.setDaemon(True)
        self.start()

    def run(self):
        try:
            while self._running:
                eieio_message = self.receive_eieio_message()
                if isinstance(eieio_message, EIEIODataMessage):
                    while eieio_message.is_next_element:
                        element = eieio_message.next_element
                        if isinstance(element, KeyDataElement):
                            self._translator.translate_control_packet(
                                MultiCastCommand(element.key))
                        elif isinstance(element, KeyPayloadDataElement):
                            self._translator.translate_control_packet(
                                MultiCastCommand(element.key, element.payload))

        except Exception:
            if self._running:
                logger.error("failure processing EIEIO message", exc_info=True)

    def close(self):
        """ Close the connection
        """
        self._running = False
        EIEIOConnection.close()

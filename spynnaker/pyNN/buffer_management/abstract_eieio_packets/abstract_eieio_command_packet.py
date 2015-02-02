from abc import abstractmethod
from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_packet import AbstractEIEIOPacket


class AbstractEIEIOCommandPacket(AbstractEIEIOPacket):

    def __init__(self, command, data=None):
        AbstractEIEIOPacket.__init__(self)
        self._header = EIEIOCommandHeader(command)
        self._message = EIEIOCommandMessage(self._header, data)

    def get_eieio_message_as_byte_array(self):
        """
        returns the eieio packet as a bytearray string
        """
        return self._message.convert_to_byte_array()

    @abstractmethod
    def is_command_packet(self):
        """
        handler for isinstance
        """

    @property
    def length(self):
        """
        :return: returns the length in bytes of the command packet
        """
        message = self._message.convert_to_byte_array()
        return len(message)
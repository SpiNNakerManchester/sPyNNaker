from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_packet import AbstractEIEIOPacket


class EIEIOCommandPacket(AbstractEIEIOPacket):

    def __init__(self, command, data=None):
        AbstractEIEIOPacket.__init__(self)
        self._header = EIEIOCommandHeader(command)
        self._message = EIEIOCommandMessage(self._header, data)

    def get_eieio_message_as_byte_array(self):
        """
        returns the eieio packet as a bytearray string
        """
        return self._message.convert_to_byte_array()

    def is_command_packet(self):
        """
        handler for isinstance
        """
        return True

    @property
    def length(self):
        """
        :return: returns the length in bytes of the command packet
        """
        message = self._message.convert_to_byte_array()
        return len(message)

    @staticmethod
    def create_command_packet_from_reader(command_number, byte_reader):
        """ Read an eieio command header from a byte reader, from which the
         initial two bytes have already been read to identify a command or a
         data packet

        :param byte1:
        :param byte2:
        :param byte_reader:
        :return:
        """
        data = byte_reader.read_bytes()
        return EIEIOCommandPacket(command_number, data)

    @staticmethod
    def get_header_size():
        return 2
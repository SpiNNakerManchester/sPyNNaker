from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_command_packet import AbstractEIEIOCommandPacket
from spynnaker.pyNN import exceptions

from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman import constants as spinnman_constants


class SequencedEIEIOSendData(AbstractEIEIOCommandPacket):

    def __init__(self, eieio_data_packet, sequence_no):
        if isinstance(eieio_data_packet, bytearray):
            self._data_packet = EIEIOMessage.create_eieio_messages_from(
                eieio_data_packet)
            self._data = eieio_data_packet
        elif isinstance(eieio_data_packet, EIEIOMessage):
            self._data_packet = eieio_data_packet
            self._data = eieio_data_packet.convert_to_byte_array()
        else:
            raise exceptions.InvalidParameterType(
                "Parameter eieio_data_packet is of an unknown type")
        AbstractEIEIOCommandPacket.__init__(
            self, spinnman_constants.EIEIO_COMMAND_IDS.NEW_BUFFERS.value,
            self._data)
        self._sequence_no = sequence_no

    @property
    def sequence_no(self):
        return self._sequence_no

    def is_command_packet(self):
        return True

    def get_eieio_message_as_byte_array(self):
        return AbstractEIEIOCommandPacket.get_eieio_message_as_byte_array(self)
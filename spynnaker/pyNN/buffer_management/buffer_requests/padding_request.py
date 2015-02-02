from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spinnman import constants as spinnman_constants

from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_command_packet import AbstractEIEIOCommandPacket


class PaddingRequest(AbstractEIEIOCommandPacket):

    def __init__(self, size_to_pad):
        AbstractEIEIOCommandPacket.__init__(
            self, spinnman_constants.EIEIO_COMMAND_IDS.EVENT_PADDING.value)
        self._size_to_pad = size_to_pad

    @property
    def size_to_pad(self):
        return self._size_to_pad

    def get_eieio_message_as_byte_array(self):
        single_message = \
            AbstractEIEIOCommandPacket.get_eieio_message_as_byte_array(self)
        number_of_repeats = self._size_to_pad / len(single_message)
        message = single_message * number_of_repeats
        return message

    def is_command_packet(self):
        return True

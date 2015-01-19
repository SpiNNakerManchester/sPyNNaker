from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spinnman import constants as spinnman_constants

from spynnaker.pyNN.buffer_management.buffer_requests.abstract_requests.abstract_command_request import AbstractCommandRequest


class EventStopRequest(AbstractCommandRequest):

    def __init__(self, chip_x, chip_y, chip_p, address_pointer, size):
        AbstractCommandRequest.__init__(self)
        self._chip_x = chip_x
        self._chip_y = chip_y
        self._chip_p = chip_p
        self._address_pointer = address_pointer
        self._size = size
        self._data = None

    @property
    def chip_x(self):
        return self._chip_x

    @property
    def chip_y(self):
        return self._chip_y

    @property
    def chip_p(self):
        return self._chip_p

    @property
    def address_pointer(self):
        return self._address_pointer

    @property
    def size(self):
        return self._size

    @property
    def data(self):
        return self._data

    def get_eieio_command_message_as_byte_array(self):
        header = EIEIOCommandHeader(
            spinnman_constants.EIEIO_COMMAND_IDS.EVENT_STOP.value)
        message = EIEIOCommandMessage(header, self._data).convert_to_byte_array()
        return message
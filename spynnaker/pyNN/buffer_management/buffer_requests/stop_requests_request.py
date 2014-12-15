from spinnman.messages.eieio.eieio_command_header import EIEIOCommandHeader
from spinnman.messages.eieio.eieio_command_message import EIEIOCommandMessage
from spinnman import constants as spinnman_constants

from spynnaker.pyNN.buffer_management.buffer_requests.abstract_data_request import \
    AbstractDataRequest


class StopRequestsRequest(AbstractDataRequest):

    def __init__(self, chip_x, chip_y, chip_p, region_id):
        AbstractDataRequest.__init__(self)
        self._chip_x = chip_x
        self._chip_y = chip_y
        self._chip_p = chip_p
        self._region_id = region_id

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
    def region_id(self):
        return self._region_id

    def get_eieio_command_message_as_byte_array(self):
        header = EIEIOCommandHeader(
            spinnman_constants.EIEIO_COMMAND_IDS.STOP_SENDING_REQUESTS.value)
        message = EIEIOCommandMessage(header, self._data).convert_to_byte_array()
        return message

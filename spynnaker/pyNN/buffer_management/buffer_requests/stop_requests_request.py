from spynnaker.pyNN.buffer_management.buffer_requests.abstract_request import \
    AbstractRequest


class StopRequestsRequest(AbstractRequest):

    def __init__(self, chip_x, chip_y, chip_p, region_id):
        AbstractRequest.__init__(self)
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

    def get_eieio_command_message(self):
        raise NotImplementedError

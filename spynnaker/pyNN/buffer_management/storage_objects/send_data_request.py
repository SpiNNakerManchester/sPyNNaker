

class SendDataRequest(object):

    def __init__(self, chip_x, chip_y, chip_p, address_pointer, data):
        self._chip_x = chip_x
        self._chip_y = chip_y
        self._chip_p = chip_p
        self._address_pointer = address_pointer
        self._data = data

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
    def data(self):
        return self._data

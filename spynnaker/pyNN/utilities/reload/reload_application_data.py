import os


class ReloadApplicationData(object):
    """ Data to be reloaded
    """

    def __init__(self, data_file, chip_x, chip_y, processor_id, base_address):
        self._data_file = data_file
        self._chip_x = chip_x
        self._chip_y = chip_y
        self._processor_id = processor_id
        self._base_address = base_address
        self._data_size = os.stat(self._data_file).st_size

    @property
    def data_file(self):
        return self._data_file

    @property
    def chip_x(self):
        return self._chip_x

    @property
    def chip_y(self):
        return self._chip_y

    @property
    def processor_id(self):
        return self._processor_id

    @property
    def base_address(self):
        return self._base_address

    @property
    def data_size(self):
        return self._data_size

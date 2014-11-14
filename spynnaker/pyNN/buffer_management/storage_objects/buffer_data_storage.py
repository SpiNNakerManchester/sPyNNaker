from collections import OrderedDict
from spynnaker.pyNN import exceptions

class BufferDataStorage(object):

    def __init__(self):
        self._buffer = OrderedDict()
        self.last_timer_tic_recorded = 0
        self._read_position_in_region = 0
        self._region_size = None
        self._region_base_address = None

    @property
    def region_size(self):
        return self._region_size

    def add_entry_to_buffer(self, buffer_key, data_piece):
        if buffer_key not in self.buffer.keys():
            self._buffer[buffer_key] = bytearray()
        self._buffer[buffer_key].append(data_piece)

    def add_entries_to_buffer(self, buffer_key, data_pieces):
        if buffer_key not in self.buffer.keys():
            self._buffer[buffer_key] = bytearray()
        self._buffer[buffer_key].extend(data_pieces)

    @property
    def region_base_address(self):
        return self._region_base_address

    def set_region_base_address(self, new_value):
        if self._region_base_address is None:
            self._region_base_address = new_value
        else:
            raise exceptions.ConfigurationException(
                "tried to set the base address of a buffer data storage region "
                "twice, this is a error due to the imutability of this "
                "parameter, please fix this issue and retry")

    @property
    def position_in_region(self):
        return self._position_in_region

    @property
    def current_absolute_address(self):
        return self._region_base_address + self._position_in_region

    def add_to_pointer(self, number_of_bytes_moved):
        self._read_position_in_region = (self._read_position_in_region +
                                         number_of_bytes_moved) % self._region_size

    @property
    def buffer(self):
        return self._buffer
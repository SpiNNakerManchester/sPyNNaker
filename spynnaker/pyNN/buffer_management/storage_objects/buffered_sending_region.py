from collections import OrderedDict
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.buffer_management.storage_objects.buffer_element import \
    BufferElement
from spynnaker.pyNN.utilities import constants
from spinnman import constants as spinnman_constants


class BufferedSendingRegion(object):

    def __init__(self):
        self._buffer = OrderedDict()
        self._read_position_in_region = 0
        self._region_size = None
        self._region_base_address = None
        self._sequence_number = 0

    def add_entry_to_buffer(self, buffer_key, data_piece):
        if buffer_key not in self.buffer.keys():
            self._buffer[buffer_key] = list()
        self._buffer[buffer_key].append(BufferElement(data_piece))

    def add_entries_to_buffer(self, buffer_key, data_pieces):
        for element in data_pieces:
            self.add_entry_to_buffer(buffer_key, element)

    def set_region_base_address(self, new_value):
        if self._region_base_address is None:
            self._region_base_address = new_value
        else:
            raise exceptions.ConfigurationException(
                "tried to set the base address of a buffer data storage region "
                "twice, this is a error due to the immutability of this "
                "parameter, please fix this issue and retry")

    def set_region_size(self, new_size):
        if self._region_size is None:
            self._region_size = new_size
        else:
            raise exceptions.ConfigurationException(
                "cannot change the region size of the region being managed by "
                "this buffered region once it has been set. ")

    def _add_to_pointer(self, number_of_bytes_moved):
        self._read_position_in_region = \
            (self._read_position_in_region + number_of_bytes_moved) \
            % self._region_size

    def get_next_timestamp(self):
        return self._buffer.items()[0][0]

    def is_region_empty(self):
        """ checks if the region is empty based from the last timer tic given
         by the core. If the last timer tic has moved, the buffer is updated
          accordingly
        :return: true if the buffer is empty, false otherwise
        :rtype: bool
        """
        if len(self._buffer) == 0:
            return True
        else:
            return False

    def is_timestamp_empty(self, timestamp):
        return timestamp in self._buffer.keys()

    def get_next_entry(self):
        timestamp = self.get_next_timestamp()
        value = self._buffer[timestamp].pop(0)
        if len(self._buffer[timestamp]) == 0:
            self._buffer.popitem(last=False)
        return value

    def get_next_sequence_no(self):
        next_seq_no = self._sequence_number
        self._sequence_number = (self._sequence_number + 1) % 256
        return next_seq_no

    @staticmethod
    def _memory_required_for_buffer(packet_buffer):
        memory_used = spinnman_constants.EIEIO_DATA_HEADER_SIZE + \
            constants.TIMESTAMP_SPACE_REQUIREMENT
        memory_used += len(packet_buffer) * constants.KEY_SIZE
        return memory_used

    @property
    def position_in_region(self):
        return self._read_position_in_region

    @property
    def current_absolute_address(self):
        return self._region_base_address + self._read_position_in_region

    @property
    def buffer(self):
        return self._buffer

    @property
    def region_size(self):
        return self._region_size

    @property
    def region_base_address(self):
        return self._region_base_address
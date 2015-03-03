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
        self._sequence_number = spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE - 1
        self._last_received_sequence_number = spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE - 1
        self._buffer_shutdown = False

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
        if not self.is_region_empty():
            return self._buffer.items()[0][0]
        else:
            return None

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
        self._sequence_number = ((self._sequence_number + 1) %
                                 spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE)
        return self._sequence_number

    def check_sequence_number(self, sequence_no):
        min_seq_no_acceptable = self._last_received_sequence_number
        max_seq_no_acceptable = (min_seq_no_acceptable + spinnman_constants.MAX_BUFFER_HISTORY) % spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE

        if min_seq_no_acceptable <= sequence_no <= max_seq_no_acceptable:
            self._last_received_sequence_number = sequence_no
            return True
        elif max_seq_no_acceptable < min_seq_no_acceptable:
            if 0 <= sequence_no <= max_seq_no_acceptable or min_seq_no_acceptable <= sequence_no <= spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE:
                self._last_received_sequence_number = sequence_no
                return True
            else:
                return False

    @staticmethod
    def _memory_required_for_buffer(packet_buffer):
        memory_used = spinnman_constants.EIEIO_DATA_HEADER_SIZE + \
            constants.TIMESTAMP_SPACE_REQUIREMENT
        memory_used += len(packet_buffer) * constants.KEY_SIZE
        return memory_used

    @property
    def sequence_number(self):
        return self._sequence_number

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

    @property
    def buffer_shutdown(self):
        return self._buffer_shutdown

    def set_buffer_shutdown(self):
        self._buffer_shutdown = True
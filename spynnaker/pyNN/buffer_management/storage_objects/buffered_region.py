from collections import OrderedDict
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import constants

class BufferedRegion(object):

    def __init__(self):
        self._buffer = OrderedDict()
        self._last_timer_tic_recorded = 0
        self._read_position_in_region = 0
        self._region_size = None
        self._region_base_address = None

    def add_entry_to_buffer(self, buffer_key, data_piece):
        if buffer_key not in self.buffer.keys():
            self._buffer[buffer_key] = bytearray()
        self._buffer[buffer_key].append(data_piece)

    def add_entries_to_buffer(self, buffer_key, data_pieces):
        if buffer_key not in self.buffer.keys():
            self._buffer[buffer_key] = bytearray()
        self._buffer[buffer_key].extend(data_pieces)

    def set_region_base_address(self, new_value):
        if self._region_base_address is None:
            self._region_base_address = new_value
        else:
            raise exceptions.ConfigurationException(
                "tried to set the base address of a buffer data storage region "
                "twice, this is a error due to the imutability of this "
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

    def is_region_empty(self, last_timer_tic):
        """ checks if the region is empty based from the last timer tic given
         by the core. If the last timer tic has moved, the buffer is updated
          accordingly

        :param last_timer_tic: the last timer tic the core thinks it
        recievced buffers from
        :type last_timer_tic: int
        :return: true if the buffer is empty, false otherwise
        :rtype: bool
        """
        if self._last_timer_tic_recorded == last_timer_tic:
            if len(self._buffer) == 0:
                return True
            else:
                return False
        else:
            #update buffer to relfect changes have taken place on core
            caught_up = False
            position_in_keys = 0
            memory_used = 0
            keys = self._buffer.keys()
            while not caught_up:
                if keys[position_in_keys] == last_timer_tic:
                    caught_up = True
                memory_used += self._memory_required_for_buffer(
                    self._buffer[keys[position_in_keys]])
                #remove entry from buffer
                del self._buffer[keys[position_in_keys]]
                position_in_keys += 1
            length_of_region_left = \
                self._region_size - (self._read_position_in_region +
                                     memory_used)
            min_memory_required_for_packet = \
                (constants.BUFFER_HEADER_SIZE +
                 constants.TIMESTAMP_SPACE_REQUIREMENT + constants.KEY_SIZE)

            if (length_of_region_left < min_memory_required_for_packet) \
                    and (length_of_region_left > 0):
                memory_used += length_of_region_left
            self._add_to_pointer(memory_used)
            # check new buffer state
            if len(self._buffer) == 0:
                return True
            else:
                return False

    @staticmethod
    def _memory_required_for_buffer(packet_buffer):
        memory_used = constants.BUFFER_HEADER_SIZE + \
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
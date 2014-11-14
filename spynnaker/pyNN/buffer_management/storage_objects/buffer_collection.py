from spinnman import exceptions as spinnman_exceptions
from spinnman.data.little_endian_byte_array_byte_writer import \
    LittleEndianByteArrayByteWriter
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.storage_objects.buffer_data_storage \
    import BufferDataStorage
from spynnaker.pyNN.buffer_management.storage_objects.send_data_request \
    import SendDataRequest
from spynnaker.pyNN.utilities import constants
import math


class BufferCollection(object):

    def __init__(self):
        self._buffers_to_transmit = dict()

    def add_buffer_element_to_transmit(self, region_id, buffer_key, data_piece):
        """ adds a buffer for a given region id

        :param region_id: the region id for which this buffer is being built
        :param buffer_key: the key for the buffer
        :param data_piece: the peice of data to add to the buffer
        :type region_id: int
        :type buffer_key: int
        :type data_piece: int
        :return: None
        :rtype: None
        """
        if region_id not in self._buffers_to_transmit.keys():
            self._buffers_to_transmit[region_id] = BufferDataStorage()
        self._buffers_to_transmit[region_id].\
            add_entry_to_buffer(buffer_key, data_piece)

    def add_buffer_elements_to_transmit(self, region_id, buffer_key,
                                        data_pieces):
        """ adds a buffer for a given region id

        :param region_id: the region id for which this buffer is being built
        :param buffer_key: the key for the buffer
        :param data_pieces: the peices of data to add to the buffer
        :type region_id: int
        :type buffer_key: int
        :type data_pieces: iterable
        :return: None
        :rtype: None
        """
        if region_id not in self._buffers_to_transmit.keys():
            self._buffers_to_transmit[region_id] = BufferDataStorage()
        self._buffers_to_transmit[region_id].\
            add_entries_to_buffer(buffer_key, data_pieces)

    def contains_key(self, key):
        if key in self._buffers_to_transmit.keys():
            return True
        return False

    def process_buffer_packet(self, buffered_packet):
        """ method to support callback for sneding new buffers down to the
         machine

        :param buffered_packet: the buffered packet from the board for this vertex
        :type buffered_packet: spynnaker.pynn.buffer_management.buffer_packet.BufferPacket
        :return: either a request or None
        """
        #check if the region has got buffers
        if buffered_packet.region_id not in self._buffers_to_transmit.keys():
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "buffered_packet.region_id",
                "The region being requested does not contain any buffered data")
        if (buffered_packet.count <
            (constants.BUFFER_HEADER_SIZE +
                constants.TIMESTAMP_SPACE_REQUIREMENT)):
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "buffered_packet.count",
                "The count is below what is needed for a eieio header, and so"
                "shouldnt have been requested")
        # if the region has no more buffers to transmit, return none
        if len(self._buffers_to_transmit[buffered_packet.region_id].buffer) == 0:
            return None

        buffer_to_transmit, memory_used = \
            self._generate_buffers_for_transmission(buffered_packet)

        address_pointer = \
            self._buffers_to_transmit[buffered_packet.region_id].\
            current_absolute_address
        self._buffers_to_transmit[buffered_packet.region_id].add_to_pointer(memory_used)
        return SendDataRequest(
            chip_x=buffered_packet.chip_x, chip_y=buffered_packet.chip_y,
            chip_p=buffered_packet.chip_p, address_pointer=address_pointer,
            data=buffer_to_transmit)

    def _generate_buffers_for_transmission(self, buffered_packet):
        #build the buffer for the size avilable
        data = LittleEndianByteArrayByteWriter()
        buffers = self._buffers_to_transmit[buffered_packet.region_id].buffer
        buffer_keys = list(buffers.keys())
        #by default there is always a eieio header (in the form of a spike train)
        memory_used = constants.BUFFER_HEADER_SIZE + \
            constants.TIMESTAMP_SPACE_REQUIREMENT
        while memory_used < buffered_packet.count:
            header_byte_1 = (1 << 5) + (1 << 4) + \
                            (EIEIOTypeParam.KEY_PAYLOAD_32_BIT.value << 2)
            buffer_length = len(buffers[buffer_keys[memory_used]]) * 4
            # check if theres enough space in buffer for packets for this
            # time stamp
            if buffer_length < buffered_packet.count:
                #check that the limit on the eieio message count is valid
                if len(buffers[buffer_keys[memory_used]]) > (math.pow(2, 8) - 1):
                    data.write_byte(math.pow(2, 8) - 1)  # header count
                    data.write_byte(header_byte_1)  # header header
                    data.write_int(buffer_keys[memory_used])  # time stamp
                    # write entries
                    for entry in range(0, math.pow(2, 8) - 1):
                        data.write_int(buffers[buffer_keys[memory_used]][entry])
                    del buffers[buffer_keys[memory_used]][0:math.pow(2, 8) - 1]
                    memory_used += (math.pow(2, 8) - 1 * 4)
                else:
                    data.write_byte(len(buffers[buffer_keys[memory_used]]))  # header count
                    data.write_byte(header_byte_1)  # header header
                    data.write_int(buffer_keys[memory_used])  # time stamp
                    # write entries
                    for entry in buffers[buffer_keys[memory_used]]:
                        data.write_int(entry)
                    del buffers[buffer_keys[memory_used]]
                    memory_used += len(buffers[buffer_keys[memory_used]]) * 4
            else:
                length_avilable = buffered_packet.count - memory_used
                entries_to_put_in = math.floor(length_avilable / 4)
                data.write_byte(entries_to_put_in)  # header count
                data.write_byte(header_byte_1)  # header header
                data.write_int(buffer_keys[memory_used])  # time stamp
                # write entries
                for entry in range(0, entries_to_put_in):
                    data.write_int(buffers[buffer_keys[memory_used]][entry])
                del buffers[buffer_keys[memory_used]][0:entries_to_put_in]
                memory_used += (entries_to_put_in * 4)
            memory_used = constants.BUFFER_HEADER_SIZE + \
                constants.TIMESTAMP_SPACE_REQUIREMENT

        return data, memory_used
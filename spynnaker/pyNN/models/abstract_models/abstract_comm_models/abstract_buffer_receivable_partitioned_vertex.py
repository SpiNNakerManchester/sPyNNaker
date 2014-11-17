from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import math
from spinnman.data.little_endian_byte_array_byte_writer import \
    LittleEndianByteArrayByteWriter
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.storage_objects.send_data_request import \
    SendDataRequest
from spynnaker.pyNN.buffer_management.storage_objects.stop_requests_request import \
    StopRequestsRequest
from spynnaker.pyNN.utilities import constants


@add_metaclass(ABCMeta)
class AbstractBufferReceivablePartitionedVertex(object):

    def __init__(self, buffer_collection):
        self._receiver_buffer_collection = buffer_collection

    @property
    def receiver_buffer_collection(self):
        return self._receiver_buffer_collection

    @abstractmethod
    def is_bufferable_receivable_partitioned_vertex(self):
        """helper method for is instance

        :return:
        """

    def process_buffer_packet(self, buffered_packet):
        # if the region has no more buffers to transmit, return none
        if self._receiver_buffer_collection.is_region_empty(
                buffered_packet.region_id, buffered_packet.last_timer_tic):
            return StopRequestsRequest(
                buffered_packet.chip_x, buffered_packet.chip_y,
                buffered_packet.chip_p, buffered_packet.region_id)

        buffer_to_transmit = \
            self._generate_buffers_for_transmission(buffered_packet)
        address_pointer = self._receiver_buffer_collection.\
            get_region_absolute_region_address(buffered_packet.region_id)
        return SendDataRequest(
            chip_x=buffered_packet.chip_x, chip_y=buffered_packet.chip_y,
            chip_p=buffered_packet.chip_p, address_pointer=address_pointer,
            data=buffer_to_transmit)

    def _generate_buffers_for_transmission(self, buffered_packet):
        """ uses the recieved buffered packet and determines what to do with it.

        :param buffered_packet: the packet which determines future actions
        :return:
        """
        #build the buffer for the size avilable
        data = LittleEndianByteArrayByteWriter()
        buffers = self._receiver_buffer_collection.get_buffer_for_region(
            buffered_packet.region_id)

        buffer_keys = list(buffers.keys())
        position_in_buffer = 0
        #by default there is always a eieio header (in the form of a spike train)
        memory_used = constants.BUFFER_HEADER_SIZE + \
            constants.TIMESTAMP_SPACE_REQUIREMENT
        while (memory_used < buffered_packet.count
               and position_in_buffer < len(buffer_keys)):
            header_byte_1 = (1 << 5) + (1 << 4) + \
                            (EIEIOTypeParam.KEY_PAYLOAD_32_BIT.value << 2)
            buffer_length = len(buffers[buffer_keys[position_in_buffer]]) \
                * constants.KEY_SIZE
            # check if theres enough space in buffer for packets for this
            # time stamp
            if buffer_length < buffered_packet.count:
                #check that the limit on the eieio message count is valid
                if (len(buffers[buffer_keys[position_in_buffer]]) >
                        (math.pow(2, 8) - 1)):
                    data.write_byte(math.pow(2, 8) - 1)  # header count
                    data.write_byte(header_byte_1)  # header header
                    data.write_int(buffer_keys[memory_used])  # time stamp
                    # write entries
                    for entry in range(0, math.pow(2, 8) - 1):
                        data.write_int(buffers[
                            buffer_keys[position_in_buffer]][entry])
                    memory_used += (math.pow(2, 8) - 1 * constants.KEY_SIZE)
                else:
                    data.write_byte(len(buffers[buffer_keys[position_in_buffer]]))  # header count
                    data.write_byte(header_byte_1)  # header header
                    data.write_int(buffer_keys[position_in_buffer])  # time stamp
                    # write entries
                    for entry in buffers[buffer_keys[position_in_buffer]]:
                        data.write_int(entry)
                    memory_used += \
                        len(buffers[buffer_keys[position_in_buffer]]) \
                        * constants.KEY_SIZE
            else:
                length_avilable = buffered_packet.count - memory_used
                entries_to_put_in = math.floor(length_avilable /
                                               constants.KEY_SIZE)
                data.write_byte(entries_to_put_in)  # header count
                data.write_byte(header_byte_1)  # header header
                data.write_int(buffer_keys[position_in_buffer])  # time stamp
                # write entries
                for entry in range(0, entries_to_put_in):
                    data.write_int(
                        buffers[buffer_keys[position_in_buffer]][entry])
                memory_used += (entries_to_put_in * constants.KEY_SIZE)
            memory_used = constants.BUFFER_HEADER_SIZE + \
                constants.TIMESTAMP_SPACE_REQUIREMENT
            position_in_buffer += 1
            #deal with padding
            length_of_region_left = self._receiver_buffer_collection.get_left_over_space(
                buffered_packet.region_id, memory_used)
            min_memory_required_for_packet = \
                (constants.BUFFER_HEADER_SIZE +
                 constants.TIMESTAMP_SPACE_REQUIREMENT + constants.KEY_SIZE)
            #add padding if needed
            if (length_of_region_left < min_memory_required_for_packet) \
                    and (length_of_region_left > 0):
                data.write_short(0)
        return data
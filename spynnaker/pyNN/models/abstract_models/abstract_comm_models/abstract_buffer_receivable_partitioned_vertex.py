from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

import math
from spinnman.data.little_endian_byte_array_byte_writer import \
    LittleEndianByteArrayByteWriter
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman import constants as spinn_man_constants
from spynnaker.pyNN.buffer_management.storage_objects.\
    send_data_request import SendDataRequest
from spynnaker.pyNN.buffer_management.buffer_requests.stop_requests_request import StopRequestsRequest
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

    def process_buffered_packet(self, buffered_packet):
        # if the region has no more buffers to transmit, return none
        if self._receiver_buffer_collection.is_region_empty(buffered_packet):
            return StopRequestsRequest(
                buffered_packet.chip_x, buffered_packet.chip_y,
                buffered_packet.chip_p, buffered_packet.region_id)
        return self._generate_buffers_for_transmission(buffered_packet)

    def _generate_buffers_for_transmission(self, buffered_packet):
        """ uses the recieved buffered packet and determines what to do with it.

        :param buffered_packet: the packet which determines future actions
        :return:
        """
        #build the buffer for the size avilable
        buffers = self._receiver_buffer_collection.get_buffer_for_region(
            buffered_packet.region_id)

        #remove received elements
        self._remove_recieved_elements(buffered_packet, buffers)

        #start
        buffer_keys = list(buffers.keys())
        position_in_buffer = 0
        seqeunce_no = buffered_packet.sequence_no
        if seqeunce_no is None:
            seqeunce_no = 0
        used_seqeunce_no = 0
        send_requests = list()
        #by default there is always a eieio header (in the form of a spike train)
        memory_used = spinn_man_constants.EIEIO_DATA_HEADER_SIZE + \
            constants.TIMESTAMP_SPACE_REQUIREMENT
        while (memory_used < buffered_packet.count
               and position_in_buffer < len(buffer_keys)
               and used_seqeunce_no < constants.MAX_SEQUENCES_PER_TRANSMISSION):
            header_byte_1 = (1 << 5) + (1 << 4) + \
                            (EIEIOTypeParam.KEY_PAYLOAD_32_BIT.value << 2)
            buffer_length = len(buffers[buffer_keys[position_in_buffer]]) \
                * constants.KEY_SIZE
            # check if theres enough space in buffer for packets for this
            # time stamp
            send_request = None
            if buffer_length < buffered_packet.count:
                send_request, used_memory, position_in_buffer = \
                    self._deal_with_entire_timer_stamp(
                        buffers, buffer_keys, position_in_buffer, header_byte_1,
                        seqeunce_no, buffered_packet)
            else:
                send_request, used_memory = self._deal_with_partial_timer_stamp(
                    buffered_packet, memory_used, header_byte_1, buffer_keys,
                    position_in_buffer, buffers, seqeunce_no)
            send_requests.append(send_request)
            memory_used += used_memory
            seqeunce_no += 1
            used_seqeunce_no += 1
            seqeunce_no = (seqeunce_no + 1) % constants.MAX_SEQUENCE_NO
        return send_requests

    def _deal_with_partial_timer_stamp(
            self, buffered_packet, memory_used, header_byte_1, buffer_keys,
            position_in_buffer, buffers, seqeunce_no):
        """ handles creating a eieio packet for a buffer which is only partially
        trnasmitted

        :param buffered_packet: the buffered packet request
        :param memory_used: the amount of memory used up with preivous eieio
        messages planned to be trnasmitted
        :param header_byte_1: the 1st byte of the eieio header
        :param buffer_keys: the ordered list of keys from the buffers (time stamps)
        :param position_in_buffer: the position in buffer keys being used
        :param buffers: the entire buffers supply.
        :param seqeunce_no: the seqeunce number of this eieio message
        :return: a send data request and a tracker of how much memory has been
        used by this method.
        """
        data = LittleEndianByteArrayByteWriter()
        length_avilable = buffered_packet.count - memory_used
        entries_to_put_in = math.floor(length_avilable /
                                       constants.KEY_SIZE)
        entries_to_store_into_udp = \
            math.floor(constants.MAX_EIEIO_ENTRIES_TO_STORE_IN_UDP,
                       constants.KEY_SIZE)
        if entries_to_put_in > entries_to_store_into_udp:
            entries_to_put_in = entries_to_store_into_udp
        data.write_byte(entries_to_put_in)  # header count
        data.write_byte(header_byte_1)  # header header
        data.write_int(buffer_keys[position_in_buffer])  # time stamp
        # write entries
        for entry in range(0, entries_to_put_in):
            data.write_int(
                buffers[buffer_keys[position_in_buffer]][entry].entry)
            buffers[buffer_keys[position_in_buffer]][entry]\
                .set_seqeuence_no(seqeunce_no)
        memory_used += (entries_to_put_in * constants.KEY_SIZE)
        address_pointer = self._receiver_buffer_collection.\
            get_region_absolute_region_address(buffered_packet.region_id)
        request = SendDataRequest(
            chip_x=buffered_packet.chip_x, chip_y=buffered_packet.chip_y,
            chip_p=buffered_packet.chip_p, address_pointer=address_pointer,
            data=data, sequence_no=seqeunce_no)
        return request, memory_used

    def _deal_with_entire_timer_stamp(
            self, buffers, buffer_keys, position_in_buffer, header_byte_1,
            seqeunce_no, buffered_packet):
        """handles creating a eieio packet for a buffer which is completly
        trnasmitted

        :param buffered_packet: the buffered packet request
        :param header_byte_1: the 1st byte of the eieio header
        :param buffer_keys: the ordered list of keys from the buffers (time stamps)
        :param position_in_buffer: the position in buffer keys being used
        :param buffers: the entire buffers supply.
        :param seqeunce_no: the seqeunce number of this eieio message
        :return: a send data request and a tracker of how much memory has been
        used by this method.
        :return: a send data request and a tracker of how much memory has been
        used by this method.
        """
        data = LittleEndianByteArrayByteWriter()
        moved_to_new_buffer = False
        entries_to_store_into_udp = \
            math.floor(constants.MAX_EIEIO_ENTRIES_TO_STORE_IN_UDP /
                       constants.KEY_SIZE)
        #check that the limit on the eieio message count is valid
        if (len(buffers[buffer_keys[position_in_buffer]]) <=
                entries_to_store_into_udp):
            entries_to_store_into_udp = \
                len(buffers[buffer_keys[position_in_buffer]])
            moved_to_new_buffer = True
        #write the header
        data.write_byte(entries_to_store_into_udp)  # header count
        data.write_byte(header_byte_1)  # header header
        data.write_int(buffer_keys[position_in_buffer])  # time stamp
        entry_counter = 0
        # write entries
        for entry_index in range(entries_to_store_into_udp):
            data.write_int(buffers[buffer_keys[position_in_buffer]]
                           [entry_counter].entry)
            buffers[buffer_keys[position_in_buffer]][entry_counter]\
                .set_seqeuence_no(seqeunce_no)
        #create request and returns stats
        if moved_to_new_buffer:
            position_in_buffer += 1
        memory_used = entries_to_store_into_udp * constants.KEY_SIZE
        address_pointer = self._receiver_buffer_collection.\
            get_region_absolute_region_address(buffered_packet.region_id)
        request = SendDataRequest(
            chip_x=buffered_packet.chip_x, chip_y=buffered_packet.chip_y,
            chip_p=buffered_packet.chip_p, address_pointer=address_pointer,
            data=data, sequence_no=seqeunce_no)
        return request, memory_used, position_in_buffer

    @staticmethod
    def _remove_recieved_elements(buffered_packet, region):
        last_seq_no_recieved = buffered_packet.sequence_no
        if last_seq_no_recieved is not None:
            keys = region.keys()
            position_in_keys = 0
            reached = False
            finished = False

            while position_in_keys < len(keys) and not finished:
                elements = region[keys[position_in_keys]]
                to_remove = list()
                #locate stuff to remove
                for element in elements:
                    if element.seqeuence_no == last_seq_no_recieved:
                        reached = True
                    if element.seqeuence_no != last_seq_no_recieved and reached:
                        finished = True
                    if not finished:
                        to_remove.append(element)
                #if everything is to be removed, remove key from dict
                if len(to_remove) == len(elements):
                    del region[keys[position_in_keys]]
                else:  # need to remvoe a subsample
                    for remove_element in to_remove:
                        region[keys[position_in_keys]].remove(remove_element)








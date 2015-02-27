from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from spynnaker.pyNN.buffer_management.buffer_data_objects.eieio_32bit.eieio_32bit_timed_payload_prefix_data_packet import \
    EIEIO32BitTimedPayloadPrefixDataPacket
from spynnaker.pyNN.buffer_management.command_objects.host_send_sequenced_data import \
    HostSendSequencedData
from spynnaker.pyNN.buffer_management.command_objects.event_stop_request \
    import EventStopRequest
from spinnman import constants as spinnman_constants
from spynnaker.pyNN.buffer_management.command_objects.stop_requests import \
    StopRequests


@add_metaclass(ABCMeta)
class AbstractBufferReceivablePartitionedVertex(object):

    def __init__(self, buffer_collection):
        self._buffers_to_send_collection = buffer_collection

    @property
    def receiver_buffer_collection(self):
        return self._buffers_to_send_collection

    @abstractmethod
    def is_bufferable_receivable_partitioned_vertex(self):
        """helper method for is instance

        :return:
        """

    def _add_host_send_sequenced_data_header(self, packets, region_id):
        sequenced_packets = list()
        for packet in packets:
            sequence_no = self._buffers_to_send_collection.\
                get_next_sequence_no_for_region(region_id)
            sequenced_packet = HostSendSequencedData(
                packet, region_id, sequence_no)
            sequenced_packets.append(sequenced_packet)

        return sequenced_packets

    def get_next_set_of_packets(self, space_available, region_id, sequence_no):
        if not self._buffers_to_send_collection.is_region_managed(region_id):
            raise  # error: region not managed asked for managed packets

        send_requests = list()

        if sequence_no is not None:
            check_value = self._buffers_to_send_collection.check_sequence_number(
                region_id, sequence_no)
            print "sequence number {0:d}, check_value {1:d}".format(sequence_no, check_value)
            if not check_value:
                return send_requests

        if not self._buffers_to_send_collection.is_region_empty(region_id):
            if sequence_no is not None:
                max_seq_no = sequence_no
                min_seq_no = (max_seq_no - spinnman_constants.MAX_BUFFER_HISTORY) % spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE
                if min_seq_no < max_seq_no:
                    if sequence_no < min_seq_no or sequence_no > max_seq_no:
                        print "dropping packet wth sequence number {0:d} and window in the range {1:d}, {2:d}".format(sequence_no, min_seq_no, max_seq_no)
                        return send_requests
                else:  # case of wrapping around interval
                    if max_seq_no > sequence_no > min_seq_no:
                        print "dropping packet wth sequence number {0:d} and window in the range {1:d}, {2:d}".format(sequence_no, min_seq_no, max_seq_no)
                        return send_requests
                self._buffers_to_send_collection.\
                    remove_packets_in_region_in_seq_no_interval(region_id, min_seq_no, sequence_no)
                if not self._buffers_to_send_collection.\
                        is_sent_packet_list_empty(region_id):
                    previous_buffers_to_send = \
                        self._buffers_to_send_collection.get_sent_packets(
                            region_id)
                    send_requests.extend(previous_buffers_to_send)

            # compute space used by packets
            used_space = 0
            for packet in send_requests:
                used_space += packet.length
            print "historical packets: {0:d}, length: {1:d}, space available: {2:d}".format(len(send_requests), used_space, space_available)
            space_available -= used_space
            number_of_historical_packets = len(send_requests)
            max_number_of_new_packets = spinnman_constants.MAX_BUFFER_HISTORY - number_of_historical_packets

            # get next set of packets to send
            new_buffers_to_send = self._generate_buffers_for_transmission(
                space_available, max_number_of_new_packets, region_id, sequence_no)

            # add sequenced header if required - if is not the initial load
            if sequence_no is not None:
                new_buffers_to_send = self._add_host_send_sequenced_data_header(
                    new_buffers_to_send, region_id)
                self._buffers_to_send_collection.add_sent_packets(
                    new_buffers_to_send, region_id)

            new_space = 0
            for packet in new_buffers_to_send:
                new_space += packet.length
            print "new packets: {0:d}, length: {1:d}, space available: {2:d}".format(len(new_buffers_to_send), new_space, space_available)

            # add set of packets to be sent to the list
            send_requests.extend(new_buffers_to_send)
            return send_requests

        # if the region has no more buffers to transmit, stop requests
        # coming from the machine
        else:
            request = StopRequests()
            send_requests.append(request)
            request = EventStopRequest()
            sequenced_request = self._add_host_send_sequenced_data_header(request, region_id)
            self._buffers_to_send_collection.add_sent_packets(sequenced_request, region_id)
            send_requests.append(sequenced_request)
            return send_requests

    def _generate_buffers_for_transmission(self, space_available, max_number_of_new_packets, region_id, sequence_no):
        """ creates a set of packets to be sent to the machine.

        :return:
        """
        send_requests = list()
        region_is_empty = self._buffers_to_send_collection.is_region_empty(region_id)

        if region_is_empty or max_number_of_new_packets <= 0:
            return send_requests

        timestamp = self._buffers_to_send_collection.get_next_timestamp(
            region_id)

        if timestamp is None:
            return send_requests

        packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)

        if sequence_no is not None:
            space_header = HostSendSequencedData.get_header_size()
        else:
            space_header = 0

        space_used = 0

        # check if there is enough space for a new packet
        if space_used + space_header + packet.length + packet.element_size >= space_available:
            return send_requests

        terminate = 0
        while not terminate:
            available_count = packet.get_available_count()
            more_elements = self._buffers_to_send_collection.is_more_elements_for_timestamp(region_id, timestamp)
            space_going_to_be_used = space_used + space_header + packet.length + packet.element_size

            if available_count > 0 and more_elements and space_available > space_going_to_be_used:
                event = self._buffers_to_send_collection.get_next_element(region_id)
                packet.insert_key(event.entry)
            else:
                send_requests.append(packet)
                space_used += packet.length + space_header

                space_going_to_be_used = space_used + space_header + EIEIO32BitTimedPayloadPrefixDataPacket.get_min_packet_length()
                region_is_empty = self._buffers_to_send_collection.is_region_empty(region_id)

                if len(send_requests) < max_number_of_new_packets and not region_is_empty and space_available > space_going_to_be_used:
                    timestamp = self._buffers_to_send_collection.get_next_timestamp(region_id)
                    packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)
                else:
                    terminate = 1

        return send_requests

        # while (space_available > space_used + space_header + packet.element_size + packet.length and len(send_requests) < max_number_of_new_packets):
        #
        #     # if there is no more space in the packet and/or if there are no
        #     # more entries for the same timestamp queue the packet, and create
        #     # a new one(if there is space), or return the current list of
        #     # packets
        #     available_count = packet.get_available_count()
        #     more_elements = self._buffers_to_send_collection.is_more_elements_for_timestamp(region_id, timestamp)
        #     # if (available_count == 0 or not more_elements or space_available < space_used + space_header + packet.length + packet.element_size):
        #     if available_count == 0 or not more_elements:
        #         space_used += packet.length + space_header
        #         send_requests.append(packet)
        #
        #         # check if there are more packets to be sent
        #         if not self._buffers_to_send_collection.is_region_empty(region_id):
        #             timestamp = self._buffers_to_send_collection.get_next_timestamp(region_id)
        #             packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)
        #
        #             # check if there is enough space for a new packet with at least one element
        #             if (space_used + space_header + packet.length + packet.element_size >= space_available):
        #                 return send_requests
        #
        #         # if there are no more events to be sent
        #         else:
        #             return send_requests
        #
        #     event = self._buffers_to_send_collection.get_next_element(region_id)
        #     packet.insert_key(event.entry)
        #
        # if len(send_requests) < max_number_of_new_packets:
        #     space_used += packet.length + space_header
        #     send_requests.append(packet)
        # return send_requests

    #     buffer_keys = list(buffers.keys())
    #     position_in_buffer = 0
    #     used_sequence_no = 0
    #
    #     memory_used = 0
    #
    #     # check if there were previous packets with a sequence number set
    #     # which represent history of packet not received by the machine
    #
    #     while (memory_used < space_available
    #            and position_in_buffer < len(buffer_keys)
    #            and used_sequence_no < constants.MAX_SEQUENCES_PER_TRANSMISSION):
    #         timestamp = buffer_keys[position_in_buffer]
    #         buffer_length = len(buffers[timestamp]) * constants.KEY_SIZE
    #         # check if there is enough space in buffer for packets for this
    #         # time stamp
    #         if buffer_length < space_available:
    #             send_request, position_in_buffer = \
    #                 self._deal_with_entire_timer_stamp(
    #                     buffers, buffer_keys, position_in_buffer, sequence_no)
    #         else:
    #             memory_available = space_available - memory_used
    #             send_request = self._deal_with_partial_timer_stamp(
    #                 buffers, buffer_keys, position_in_buffer, sequence_no,
    #                 memory_available)
    #         send_requests.append(send_request)
    #         memory_used += send_request.length
    #         if (position_in_buffer == len(buffer_keys) and
    #                 memory_used < space_available):
    #
    #             end_request = EventStopRequest()
    #             send_requests.append(end_request)
    #             memory_used += end_request.length
    #
    #         used_sequence_no += 1
    #         if sequence_no is not None:
    #             sequence_no += 1
    #             sequence_no = (sequence_no + 1) % constants.MAX_SEQUENCE_NO
    #
    #     return send_requests
    #
    # def _deal_with_partial_timer_stamp(
    #         self, buffers, buffer_keys, position_in_buffer, sequence_no,
    #         memory_available):
    #     """ handles creating a eieio packet for a buffer which is only partially
    #     transmitted
    #
    #     :param buffered_packet: the buffered packet request
    #     :param memory_available: the amount of memory used up with previous eieio
    #     messages planned to be transmitted
    #     :param header_byte_1: the 1st byte of the eieio header
    #     :param buffer_keys: the ordered list of keys from the buffers \
    #     (time stamps)
    #     :param position_in_buffer: the position in buffer keys being used
    #     :param buffers: the entire buffers supply.
    #     :param sequence_no: the sequence number of this eieio message
    #     :return: a send data request and a tracker of how much memory has been
    #     used by this method.
    #     """
    #     timestamp = buffer_keys[position_in_buffer]
    #     packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)
    #
    #     entries_to_put_in = math.floor((memory_available - packet.header_size) /
    #                                    packet.key_size)
    #     entries_to_store_into_udp = packet.get_max_count()
    #     if entries_to_put_in > entries_to_store_into_udp:
    #         entries_to_put_in = entries_to_store_into_udp
    #
    #     # write entries
    #     for entry in range(0, entries_to_put_in):
    #         packet.insert_key(buffers[timestamp][entry].entry)
    #         if sequence_no is not None:
    #             buffers[timestamp][entry].set_seqeuence_no(sequence_no)
    #         else:
    #             buffers[timestamp][entry].set_seqeuence_no(0)
    #
    #     # if a sequence number is passed, generate a sequenced eieio packet
    #     # otherwise return packet as it is
    #     if sequence_no is not None:
    #         sequenced_packet = HostSendSequencedData(packet, sequence_no)
    #         packet = sequenced_packet
    #
    #     return packet
    #
    # def _deal_with_entire_timer_stamp(
    #         self, buffers, buffer_keys, position_in_buffer, sequence_no):
    #     """handles creating a eieio packet for a buffer which is completely
    #     transmitted
    #
    #     :param buffered_packet: the buffered packet request
    #     :param buffer_keys: the ordered list of keys from the buffers (time stamps)
    #     :param position_in_buffer: the position in buffer keys being used
    #     :param buffers: the entire buffers supply.
    #     :param sequence_no: the sequence number of this eieio message
    #     :return: a send data request and a tracker of how much memory has been
    #     used by this method.
    #     :return: a send data request and a tracker of how much memory has been
    #     used by this method.
    #     """
    #     moved_to_new_buffer = False
    #     timestamp = buffer_keys[position_in_buffer]
    #     # write the header
    #     packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)
    #     max_entries_in_packet = packet.get_max_count()
    #
    #     # check that the limit on the eieio message count is valid
    #     if len(buffers[timestamp]) <= max_entries_in_packet:
    #         max_entries_in_packet = len(buffers[timestamp])
    #         moved_to_new_buffer = True
    #     entry_counter = 0
    #
    #     # write entries
    #     for entry_index in range(max_entries_in_packet):
    #         key = buffers[timestamp][entry_index].entry
    #         packet.insert_key(key)
    #         if sequence_no is not None:
    #             buffers[timestamp][entry_index].set_seqeuence_no(sequence_no)
    #         else:
    #             buffers[timestamp][entry_index].set_seqeuence_no(0)
    #
    #     # if a sequence number is passed, generate a sequenced eieio packet
    #     # otherwise return packet as it is
    #     if sequence_no is not None:
    #         sequenced_packet = HostSendSequencedData(packet, sequence_no)
    #         packet = sequenced_packet
    #
    #     # create request and returns stats
    #     if moved_to_new_buffer:
    #         position_in_buffer += 1
    #
    #     return packet, position_in_buffer

    # @staticmethod
    # def _remove_received_elements(region, sequence_no):
    #     if sequence_no is not None:
    #         keys = region.keys()
    #         position_in_keys = 0
    #         reached = False
    #         finished = False
    #
    #         while position_in_keys < len(keys) and not finished:
    #             elements = region[keys[position_in_keys]]
    #             to_remove = list()
    #             # locate stuff to remove
    #             for element in elements:
    #                 if element.seqeuence_no == sequence_no:
    #                     reached = True
    #                 if element.seqeuence_no != sequence_no and reached:
    #                     finished = True
    #                 if not finished:
    #                     to_remove.append(element)
    #             # if everything is to be removed, remove key from dict
    #             if len(to_remove) == len(elements):
    #                 del region[keys[position_in_keys]]
    #             else:  # need to remove a subsample
    #                 for remove_element in to_remove:
    #                     region[keys[position_in_keys]].remove(remove_element)

from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import math

from spynnaker.pyNN.buffer_management.buffer_data_objects.eieio_32bit.eieio_32bit_timed_payload_prefix_data_packet import \
    EIEIO32BitTimedPayloadPrefixDataPacket
from spynnaker.pyNN.buffer_management.command_objects.host_send_sequenced_data import \
    HostSendSequencedData
from spynnaker.pyNN.buffer_management.command_objects.event_stop_request \
    import EventStopRequest
from spynnaker.pyNN.utilities import constants


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

    def get_next_set_of_packets(self, region_size, region_id, sequence_no):
        # get all the buffers for the subvertex
        buffers = self._buffers_to_send_collection.get_buffer_for_region(
            region_id)

        # if there is a sequence number, eliminate all the packets which
        # have already been acknowledged but the spinnaker machine
        if sequence_no is not None:
            self._remove_received_elements(region_id, sequence_no)

        # if the region has no more buffers to transmit, stop requests
        # coming from the machine
        if self._buffers_to_send_collection.is_region_empty(region_id):
            send_requests = list()
            request = EventStopRequest()
            send_requests.append(request)
            return send_requests

        else:
            return self._generate_buffers_for_transmission(
                buffers, region_size, sequence_no)

    def _generate_buffers_for_transmission(
            self, buffers, region_size, sequence_no):
        """ uses the received buffered packet and determines what to do with it.

        :param buffered_packet: the packet which determines future actions
        :return:
        """
        buffer_keys = list(buffers.keys())
        position_in_buffer = 0
        used_sequence_no = 0
        send_requests = list()
        memory_used = 0

        # check if there were previous packets with a sequence number set
        # which represent history of packet not received by the machine

        while (memory_used < region_size
               and position_in_buffer < len(buffer_keys)
               and used_sequence_no < constants.MAX_SEQUENCES_PER_TRANSMISSION):
            timestamp = buffer_keys[position_in_buffer]
            buffer_length = len(buffers[timestamp]) * constants.KEY_SIZE
            # check if there is enough space in buffer for packets for this
            # time stamp
            if buffer_length < region_size:
                send_request, position_in_buffer = \
                    self._deal_with_entire_timer_stamp(
                        buffers, buffer_keys, position_in_buffer, sequence_no)
            else:
                memory_available = region_size - memory_used
                send_request = self._deal_with_partial_timer_stamp(
                    buffers, buffer_keys, position_in_buffer, sequence_no,
                    memory_available)
            send_requests.append(send_request)
            memory_used += send_request.length
            if (position_in_buffer == len(buffer_keys) and
                    memory_used < region_size):

                end_request = EventStopRequest()
                send_requests.append(end_request)
                memory_used += end_request.length

            used_sequence_no += 1
            if sequence_no is not None:
                sequence_no += 1
                sequence_no = (sequence_no + 1) % constants.MAX_SEQUENCE_NO

        return send_requests

    def _deal_with_partial_timer_stamp(
            self, buffers, buffer_keys, position_in_buffer, sequence_no,
            memory_available):
        """ handles creating a eieio packet for a buffer which is only partially
        transmitted

        :param buffered_packet: the buffered packet request
        :param memory_available: the amount of memory used up with previous eieio
        messages planned to be transmitted
        :param header_byte_1: the 1st byte of the eieio header
        :param buffer_keys: the ordered list of keys from the buffers \
        (time stamps)
        :param position_in_buffer: the position in buffer keys being used
        :param buffers: the entire buffers supply.
        :param sequence_no: the sequence number of this eieio message
        :return: a send data request and a tracker of how much memory has been
        used by this method.
        """
        timestamp = buffer_keys[position_in_buffer]
        packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)

        entries_to_put_in = math.floor((memory_available - packet.header_size) /
                                       packet.key_size)
        entries_to_store_into_udp = packet.get_max_count()
        if entries_to_put_in > entries_to_store_into_udp:
            entries_to_put_in = entries_to_store_into_udp

        # write entries
        for entry in range(0, entries_to_put_in):
            packet.insert_key(buffers[timestamp][entry].entry)
            if sequence_no is not None:
                buffers[timestamp][entry].set_seqeuence_no(sequence_no)
            else:
                buffers[timestamp][entry].set_seqeuence_no(0)

        # if a sequence number is passed, generate a sequenced eieio packet
        # otherwise return packet as it is
        if sequence_no is not None:
            sequenced_packet = HostSendSequencedData(packet, sequence_no)
            packet = sequenced_packet

        return packet

    def _deal_with_entire_timer_stamp(
            self, buffers, buffer_keys, position_in_buffer, sequence_no):
        """handles creating a eieio packet for a buffer which is completely
        transmitted

        :param buffered_packet: the buffered packet request
        :param buffer_keys: the ordered list of keys from the buffers (time stamps)
        :param position_in_buffer: the position in buffer keys being used
        :param buffers: the entire buffers supply.
        :param sequence_no: the sequence number of this eieio message
        :return: a send data request and a tracker of how much memory has been
        used by this method.
        :return: a send data request and a tracker of how much memory has been
        used by this method.
        """
        moved_to_new_buffer = False
        timestamp = buffer_keys[position_in_buffer]
        # write the header
        packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)
        max_entries_in_packet = packet.get_max_count()

        # check that the limit on the eieio message count is valid
        if len(buffers[timestamp]) <= max_entries_in_packet:
            max_entries_in_packet = len(buffers[timestamp])
            moved_to_new_buffer = True
        entry_counter = 0

        # write entries
        for entry_index in range(max_entries_in_packet):
            key = buffers[timestamp][entry_index].entry
            packet.insert_key(key)
            if sequence_no is not None:
                buffers[timestamp][entry_index].set_seqeuence_no(sequence_no)
            else:
                buffers[timestamp][entry_index].set_seqeuence_no(0)

        # if a sequence number is passed, generate a sequenced eieio packet
        # otherwise return packet as it is
        if sequence_no is not None:
            sequenced_packet = HostSendSequencedData(packet, sequence_no)
            packet = sequenced_packet

        # create request and returns stats
        if moved_to_new_buffer:
            position_in_buffer += 1

        return packet, position_in_buffer

    @staticmethod
    def _remove_received_elements(region, sequence_no):
        if sequence_no is not None:
            keys = region.keys()
            position_in_keys = 0
            reached = False
            finished = False

            while position_in_keys < len(keys) and not finished:
                elements = region[keys[position_in_keys]]
                to_remove = list()
                # locate stuff to remove
                for element in elements:
                    if element.seqeuence_no == sequence_no:
                        reached = True
                    if element.seqeuence_no != sequence_no and reached:
                        finished = True
                    if not finished:
                        to_remove.append(element)
                # if everything is to be removed, remove key from dict
                if len(to_remove) == len(elements):
                    del region[keys[position_in_keys]]
                else:  # need to remove a subsample
                    for remove_element in to_remove:
                        region[keys[position_in_keys]].remove(remove_element)

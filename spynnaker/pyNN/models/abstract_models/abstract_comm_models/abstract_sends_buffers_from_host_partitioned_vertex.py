from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
import math
import logging

from spinnman.messages.eieio.buffer_data_objects.eieio_32bit.\
    eieio_32bit_timed_payload_prefix_data_packet import \
    EIEIO32BitTimedPayloadPrefixDataPacket
from spinnman.messages.eieio.command_objects.host_send_sequenced_data import \
    HostSendSequencedData
from spinnman.messages.eieio.command_objects.event_stop_request import \
    EventStopRequest
from spinnman import constants as spinnman_constants
from spinnman.messages.eieio.command_objects.stop_requests import \
    StopRequests


logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractSendsBuffersFromHostPartitionedVertex(object):

    def __init__(self, buffer_collection):
        self._buffers_to_send_collection = buffer_collection

    @property
    def sender_buffer_collection(self):
        return self._buffers_to_send_collection

    @abstractmethod
    def is_sends_buffers_from_host_partitioned_vertex(self):
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

    def get_next_set_of_packets(
            self, space_available, region_id, sequence_no,
            routing_infos, partitioned_graph):
        if not self._buffers_to_send_collection.is_region_managed(region_id):
            raise  # error: region not managed asked for managed packets

        send_requests = list()

        if sequence_no is not None:
            check_value = self._buffers_to_send_collection.\
                check_sequence_number(region_id, sequence_no)
            logger.debug("sequence number {0:d}, check_value {1:d}".format(
                sequence_no, check_value))
            if not check_value:
                return send_requests

        if not self._buffers_to_send_collection.is_region_empty(region_id):
            logger.debug("region {0:d} is not empty".format(region_id))
            if sequence_no is not None:
                max_seq_no = sequence_no
                min_seq_no = ((max_seq_no -
                               spinnman_constants.MAX_BUFFER_HISTORY) %
                              spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE)
                if min_seq_no < max_seq_no:
                    if sequence_no < min_seq_no or sequence_no > max_seq_no:
                        logger.debug("dropping packet wth sequence number "
                                     "{0:d} and window in the range {1:d}, "
                                     "{2:d}".format(sequence_no, min_seq_no,
                                                    max_seq_no))
                        return send_requests
                else:  # case of wrapping around interval
                    if max_seq_no > sequence_no > min_seq_no:
                        logger.debug("dropping packet wth sequence number "
                                     "{0:d} and window in the range {1:d}, "
                                     "{2:d}".format(sequence_no, min_seq_no,
                                                    max_seq_no))
                        return send_requests
                self._buffers_to_send_collection.\
                    remove_packets_in_region_in_seq_no_interval(
                        region_id, min_seq_no, sequence_no)
                if not self._buffers_to_send_collection.\
                        is_sent_packet_list_empty(region_id):
                    previous_buffers_to_send = \
                        self._buffers_to_send_collection.get_sent_packets(
                            region_id)
                    send_requests.extend(previous_buffers_to_send)

            # compute space used by packets
            logger.debug("computing space used by {0:d} packets".format(
                len(send_requests)))
            used_space = 0
            for packet in send_requests:
                used_space += packet.length
            logger.debug("historical packets: {0:d}, length: {1:d}, "
                         "space available: {2:d}".format(
                             len(send_requests), used_space, space_available))
            space_available -= used_space
            number_of_historical_packets = len(send_requests)
            max_number_of_new_packets = (spinnman_constants.MAX_BUFFER_HISTORY -
                                         number_of_historical_packets)

            # get next set of packets to send
            new_buffers_to_send = self._generate_buffers_for_transmission(
                space_available, max_number_of_new_packets, region_id,
                sequence_no, routing_infos, partitioned_graph)

            # add sequenced header if required - if is not the initial load
            if sequence_no is not None:
                new_buffers_to_send = self._add_host_send_sequenced_data_header(
                    new_buffers_to_send, region_id)
                self._buffers_to_send_collection.add_sent_packets(
                    new_buffers_to_send, region_id)

            new_space = 0
            for packet in new_buffers_to_send:
                new_space += packet.length
            logger.debug("new packets: {0:d}, length: {1:d}, space available: "
                         "{2:d}".format(len(new_buffers_to_send), new_space,
                                        space_available))

            # add set of packets to be sent to the list
            send_requests.extend(new_buffers_to_send)
            return send_requests

        # if the region has no more buffers to transmit, stop requests
        # coming from the machine
        else:
            logger.debug("region {0:d} is empty".format(region_id))
            if not self._buffers_to_send_collection.buffer_shutdown(region_id):
                request = EventStopRequest()
                send_requests.append(request)
                send_requests = self._add_host_send_sequenced_data_header(
                    send_requests, region_id)
                self._buffers_to_send_collection.add_sent_packets(
                    send_requests, region_id)
                self._buffers_to_send_collection.set_buffer_shutdown(region_id)
                logger.debug("sending buffered application shutdown command")
            else:
                request = StopRequests()
                send_requests.append(request)
                logger.debug("sending stop requests command")
            logger.debug("returning {0:d} packets".format(len(send_requests)))
            return send_requests

    def _generate_buffers_for_transmission(
            self, space_available, max_number_of_new_packets, region_id,
            sequence_no, routing_infos, partitioned_graph):
        """ creates a set of packets to be sent to the machine.

        :return:
        """
        send_requests = list()
        region_is_empty = self._buffers_to_send_collection.is_region_empty(
            region_id)

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
            # the number of packet loaded at the first instance, when the
            # system is still in a wait state, does not influence the
            # performance of the execution
            max_number_of_new_packets = int(math.ceil(
                space_available / packet.get_min_packet_length()))
            space_header = 0

        space_used = 0

        # check if there is enough space for a new packet
        if (space_used + space_header + packet.length +
                packet.element_size > space_available):
            return send_requests

        terminate = 0
        while not terminate:
            available_count = packet.get_available_count()
            more_elements = self._buffers_to_send_collection.\
                is_more_elements_for_timestamp(region_id, timestamp)
            space_going_to_be_used = (space_used + space_header +
                                      packet.length + packet.element_size)

            if (available_count > 0 and more_elements and
                    space_available >= space_going_to_be_used):
                event = self._buffers_to_send_collection.get_next_element(
                    region_id)
                # or the event with the base routing key
                subvertex = self._buffers_to_send_collection.managed_vertex
                first_outgoing_edge = partitioned_graph.\
                    outgoing_subedges_from_subvertex(subvertex)[0]
                # subedge_routing_info = routing_infos.\
                #     get_subedge_information_from_subedge(first_outgoing_edge)
                base_routing_key = routing_infos.get_key_from_subedge(
                    first_outgoing_edge)
                final_routing_key = base_routing_key | event.entry
                packet.insert_key(final_routing_key)
            else:
                send_requests.append(packet)
                space_used += packet.length + space_header

                space_going_to_be_used = (
                    space_used + space_header +
                    EIEIO32BitTimedPayloadPrefixDataPacket.
                    get_min_packet_length())
                region_is_empty = self._buffers_to_send_collection.\
                    is_region_empty(region_id)

                if (len(send_requests) < max_number_of_new_packets and
                        not region_is_empty and
                        space_available > space_going_to_be_used):
                    timestamp = self._buffers_to_send_collection.\
                        get_next_timestamp(region_id)
                    packet = EIEIO32BitTimedPayloadPrefixDataPacket(timestamp)
                else:
                    terminate = 1

        return send_requests

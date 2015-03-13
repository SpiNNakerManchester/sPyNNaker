import logging

from spinnman.messages.eieio.command_objects.host_send_sequenced_data import \
    HostSendSequencedData
from spinnman import constants as spinnman_constants
from spynnaker.pyNN import exceptions

logger = logging.getLogger(__name__)


class BuffersSentDeque(object):
    def __init__(self):
        self._buffers_sent = list()

    def add_packet(self, packet):
        self._buffers_sent.append(packet)

    def add_packets(self, packets):
        if not isinstance(packets, list):
            raise  # wrong type of parameter in the call
        else:
            for packet in packets:
                self.add_packet(packet)

    def remove_packets_in_seq_no_interval(self, min_seq_no, max_seq_no):
        if self.is_empty():
            return

        packet_set = range(len(self._buffers_sent) - 1, -1, -1)
        logger.debug("removing packets from seq_no {0:d} to seq_no {1:d}".
                     format(min_seq_no, max_seq_no))
        logger.debug("range: {0:s}".format(packet_set))
        for i in packet_set:
            logger.debug("packet with seq_no: {0:d}".
                         format(self._buffers_sent[i].sequence_no))
            if isinstance(self._buffers_sent[i], HostSendSequencedData):
                if min_seq_no < max_seq_no:
                    if (min_seq_no <= self._buffers_sent[i].sequence_no <=
                            max_seq_no):
                        packet = self._buffers_sent.pop(i)
                        logger.debug("1 - popped packet with sequence number "
                                     "{0:d}, with interval {1:d} to {2:d}".
                                     format(packet.sequence_no, min_seq_no,
                                            max_seq_no))
                else:  # case of wrapping around interval
                    if (min_seq_no <= self._buffers_sent[i].sequence_no <=
                            spinnman_constants.SEQUENCE_NUMBER_MAX_VALUE):
                        packet = self._buffers_sent.pop(i)
                        logger.debug("2 - popped packet with sequence number "
                                     "{0:d}, with interval {1:d} to {2:d}".
                                     format(packet.sequence_no, min_seq_no,
                                            max_seq_no))
                    elif 0 <= self._buffers_sent[i].sequence_no <= max_seq_no:
                        packet = self._buffers_sent.pop(i)
                        logger.debug("3 - popped packet with sequence number "
                                     "{0:d}, with interval {1:d} to {2:d}".
                                     format(packet.sequence_no, min_seq_no,
                                            max_seq_no))
            else:
                # error on the type of packet in the queue - there should only
                # ever be sequenced packets
                raise exceptions.InvalidPacketType(
                    "Invalid packet type in sequenced queue: the sent packet "
                    "queue should only ever contain sequenced packets")

    def get_packets(self):
        return_list = list()
        for packet in self._buffers_sent:
            return_list.append(packet)
        return return_list

    def is_empty(self):
        if self._buffers_sent:
            return False
        else:
            return True

    def get_min_seq_no(self):
        if self._buffers_sent:
            return self._buffers_sent[0].sequence_no
        else:
            return None
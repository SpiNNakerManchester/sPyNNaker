from collections import deque
from spynnaker.pyNN.buffer_management.command_objects.host_send_sequenced_data import \
    HostSendSequencedData


class BuffersSentDeque(object):
    def __init__(self):
        self._buffers_sent = deque()

    def add_packet(self, packet):
        self._buffers_sent.append(packet)

    def add_packets(self, packets):
        if not isinstance(packets, list):
            raise  # wrong type of parameter in the call
        else:
            for packet in packets:
                self.add_packet(packet)

    def remove_packets_up_to_seq_no(self, seq_no):
        if seq_no == 0:
            seq_no = 256
        while self._buffers_sent:
            if isinstance(self._buffers_sent[0], HostSendSequencedData):
                if self._buffers_sent[0].sequence_no <= seq_no:
                    _ = self._buffers_sent.popleft()
                else:
                    break
            else:
                raise  # error on the type of packet in the queue - there should only ever be sequenced packets

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

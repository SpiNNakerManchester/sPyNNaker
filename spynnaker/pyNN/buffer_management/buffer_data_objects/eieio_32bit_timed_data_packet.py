from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_data_packet import AbstractEIEIODataPacket


class EIEIO32BitTimedDataPacket(AbstractEIEIODataPacket):

    def __init__(self, pkt_time, data=None):
        if data is None:
            data = bytearray()

        AbstractEIEIODataPacket.__init__(self, EIEIOTypeParam.KEY_32_BIT,
                                         payload_base=pkt_time, is_time=True,
                                         data=data)

    def get_eieio_message_as_byte_array(self):
        """
        returns the eieio packet as a bytearray string
        """
        return self._message.convert_to_byte_array()

    def insert_key(self, key):
        if self.get_available_count() > 0:  # there is space available
            self._insert_key(key)
            self._length += self._element_size
            return True
        else:
            return False

    @property
    def pkt_time(self):
        return AbstractEIEIODataPacket(self).payload_base

    @property
    def length(self):
        return self._length

    def is_data_packet(self):
        """
        handler for isinstance
        """
        return True
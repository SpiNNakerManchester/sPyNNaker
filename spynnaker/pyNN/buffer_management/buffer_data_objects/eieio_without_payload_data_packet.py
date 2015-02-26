from abc import abstractmethod
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_data_packet import AbstractEIEIODataPacket


class EIEIOWithoutPayloadDataPacket(AbstractEIEIODataPacket):

    def __init__(self, type_param, prefix_param=None, payload_base=None,
                 prefix_type=None, is_time=False, data=None):
        if data is None:
            data = bytearray()

        if (type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT or
                type_param == EIEIOTypeParam.KEY_PAYLOAD_32_BIT):
            raise  # wrong type of packet

        AbstractEIEIODataPacket.__init__(
            self, type_param, prefix_param=prefix_param,
            payload_base=payload_base, prefix_type=prefix_type, is_time=is_time,
            data=data)

    def insert_key(self, key):
        if self.get_available_count() > 0:  # there is space available
            self._insert_key(key)
            self._length += self._element_size
            return True
        else:
            return False

    @staticmethod
    def get_min_length(type_param, tag_param=0, prefix_param=None,
                       payload_base=None, prefix_type=None, is_time=False):
        if (type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT or
                type_param == EIEIOTypeParam.KEY_PAYLOAD_32_BIT):
            raise  # wrong type of packet
        return AbstractEIEIODataPacket.get_min_length(
            type_param, tag_param=tag_param, prefix_param=prefix_param,
            payload_base=payload_base, prefix_type=prefix_type, is_time=is_time)

    @staticmethod
    @abstractmethod
    def get_min_packet_length():
        pass

    @property
    def length(self):
        return self._length

    def is_data_packet(self):
        """
        handler for isinstance
        """
        return True

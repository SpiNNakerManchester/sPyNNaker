from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman.messages.eieio.eieio_prefix_type import EIEIOPrefixType
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_data_packet import AbstractEIEIODataPacket


class EIEIO32BitWithPayloadLowerKeyPrefixDataPacket(AbstractEIEIODataPacket):

    def __init__(self, key_prefix, data=None):
        if data is None:
            data = bytearray()

        AbstractEIEIODataPacket.__init__(
            self, EIEIOTypeParam.KEY_PAYLOAD_32_BIT, prefix_param=key_prefix,
            prefix_type=EIEIOPrefixType.LOWER_HALF_WORD, data=data)

    def insert_key_and_payload(self, key, payload):
        if self.get_available_count() > 0:  # there is space available
            AbstractEIEIODataPacket(self)._insert_key_and_payload(key, payload)
            self._length += self._element_size
            return True
        else:
            return False

    @property
    def key_prefix(self):
        return AbstractEIEIODataPacket(self).prefix_param

    @property
    def length(self):
        return self._length

    def is_data_packet(self):
        """
        handler for isinstance
        """
        return True
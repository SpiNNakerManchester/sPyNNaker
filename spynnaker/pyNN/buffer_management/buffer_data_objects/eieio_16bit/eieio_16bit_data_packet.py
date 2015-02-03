from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_data_packet import AbstractEIEIODataPacket


class EIEIO16BitDataPacket(AbstractEIEIODataPacket):

    def __init__(self, data=None):
        if data is None:
            data = bytearray()

        AbstractEIEIODataPacket.__init__(self, EIEIOTypeParam.KEY_16_BIT,
                                         data=data)

    def insert_key(self, key):
        if self.get_available_count() > 0:  # there is space available
            AbstractEIEIODataPacket(self)._insert_key(key)
            self._length += self._element_size
            return True
        else:
            return False

    @property
    def length(self):
        return self._length

    def is_data_packet(self):
        """
        handler for isinstance
        """
        return True

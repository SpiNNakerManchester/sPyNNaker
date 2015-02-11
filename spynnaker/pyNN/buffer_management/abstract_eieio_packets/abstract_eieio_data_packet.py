from abc import abstractmethod
from spinnman import exceptions as spinnman_exceptions
from spinnman.data.little_endian_byte_array_byte_reader import \
    LittleEndianByteArrayByteReader
from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spinnman import constants as spinnman_constants
import math
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.abstract_eieio_packet import \
    AbstractEIEIOPacket


class AbstractEIEIODataPacket(AbstractEIEIOPacket):

    def __init__(self, type_param, tag_param=0, prefix_param=None,
                 payload_base=None, prefix_type=None, is_time=False, data=None):

        AbstractEIEIOPacket.__init__(self)

        self._header = EIEIOHeader(
            type_param, tag_param, prefix_param, payload_base,
            prefix_type, is_time)

        self._message = EIEIOMessage(
            eieio_header=self._header, data=data)

        self._header_size = 2

        if type_param == EIEIOTypeParam.KEY_16_BIT:
            self._key_size = 2
            self._element_size = 2
        elif type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT:
            self._key_size = 2
            self._element_size = 4
        elif type_param == EIEIOTypeParam.KEY_32_BIT:
            self._key_size = 4
            self._element_size = 4
        elif type_param == EIEIOTypeParam.KEY_PAYLOAD_32_BIT:
            self._key_size = 4
            self._element_size = 8
        else:
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "variable type_param", "unknown type")

        self._base_size = self._header_size
        if prefix_param is not None:
            self._base_size += 2

        if payload_base is not None:
            self._base_size += self._key_size

        self._length = self._base_size + len(data)

    def _insert_key(self, key):
        self._message.write_data(key)

    def _insert_key_and_payload(self, key, payload):
        self._message.write_data(key, payload)

    def get_available_count(self):
        available_payload_space = (spinnman_constants.UDP_MESSAGE_MAX_SIZE -
                                   self._length)
        max_float = math.floor(available_payload_space / self._element_size)
        max_count = int(max_float)
        return max_count

    def get_max_count(self):
        """
        :return: maximum number of entries that this type of eieio packet type
        can handle
        """
        available_payload_space = (spinnman_constants.UDP_MESSAGE_MAX_SIZE -
                                   self._base_size)
        max_float = math.floor(available_payload_space / self._element_size)
        max_count = int(max_float)
        return max_count

    def get_next_element(self):
        if self.has_key_prefix:
            key_prefix = self.key_prefix
        else:
            key_prefix = 0

        if self.has_payload_prefix:
            payload_prefix = self.payload_prefix
        else:
            payload_prefix = 0

        element_count = self._header.count_param
        data_reader = LittleEndianByteArrayByteReader(self._message.data)
        if (self._header.type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT
                or self._header.type_param ==
                EIEIOTypeParam.KEY_PAYLOAD_32_BIT):
            for i in xrange(element_count):
                if self._key_size == 2:
                    key = data_reader.read_short()
                    payload = data_reader.read_short()
                else:
                    key = data_reader.read_int()
                    payload = data_reader.read_int()

                key |= key_prefix
                payload |= payload_prefix

                yield key, payload

        else:
            for i in xrange(element_count):
                if self._key_size == 2:
                    key = data_reader.read_short()
                else:
                    key = data_reader.read_int()

                key |= key_prefix

                if self.has_payload_prefix:
                    yield key, payload_prefix
                else:
                    yield key

    @property
    def length(self):
        return self._length

    @property
    def element_size(self):
        """
        :return: returns the size in bytes of each element in the packet \
        (including payload, if present)
        """
        return self._element_size

    @property
    def key_size(self):
        """
        :return: returns the size in bytes of the key used in the packet
        """
        return self._key_size

    @property
    def header_size(self):
        """
        :return: returns the size in bytes of the header
        """
        return self._base_size

    def get_eieio_message_as_byte_array(self):
        """
        returns the eieio packet as a bytearray string
        """
        return self._message.convert_to_byte_array()

    @abstractmethod
    def is_data_packet(self):
        """
        handler for isinstance
        """

    # query constructor parameters
    @property
    def prefix_param(self):
        return self._header.prefix_param

    @property
    def payload_base(self):
        return self._header.payload_base

    @property
    def prefix_type(self):
        return self._header.prefix_type

    @property
    def is_time(self):
        return self._header.is_time

    # user queries
    @property
    def has_payload(self):
        if (self._header.type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT or
                self._header.type_param == EIEIOTypeParam.KEY_PAYLOAD_32_BIT):
            return True
        else:
            if self.has_payload_prefix:
                return True
            else:
                return False

    @property
    def has_payload_prefix(self):
        if self.payload_base is not None:
            return False
        else:
            return True

    @property
    def has_fixed_timestamp(self):
        if self.is_time:
            return self.has_payload_prefix
        else:
            return False

    @property
    def has_key_prefix(self):
        if self.key_prefix is not None:
            return False
        else:
            return True

    @property
    def is_timed(self):
        return self.is_time

    @property
    def payload_prefix(self):
        if self.has_payload_prefix:
            return self.payload_base
        else:
            return None

    @property
    def timestamp(self):
        if self.is_time:
            return self.payload_prefix
        else:
            return None

    @property
    def key_prefix(self):
        if self.has_key_prefix:
            return self.prefix_param
        else:
            return None


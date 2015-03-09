from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass
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


@add_metaclass(ABCMeta)
class AbstractEIEIODataPacket(AbstractEIEIOPacket):
    """
    This class represent a generic eieio data packet used in the communication
    with the SpiNNaker machine
    """

    def __init__(self, type_param, tag_param=0, prefix_param=None,
                 payload_base=None, prefix_type=None, is_time=False, data=None):
        """

        :param type_param: type of packet: 16- or 32-bit events with or
                           without payload
        :type type_param: spinnman.messages.eieio.eieio_type_param.\
                          EIEIOTypeParam
        :param tag_param: tag parameter of the eieio header (currently unused)
        :type tag_param: 2-bit unsigned int
        :param prefix_param: base value to be used in the construction of the \
                             event to be multicasted
        :type prefix_param: 16-bit unsigned int
        :param payload_base: base value to be used in the construction of the \
                             payload to the event to be multicasted
        :param prefix_type: determines if the prefix_param value has to be \
                            applied on the upper or lower part of the \
                            multicast routing key
        :type prefix_type: spinnman.spinnman.messages.eieio.eieio_prefix_type
        :param is_time: determines if the payload represents a timestamp
        :type is_time: bool
        :param data: payload to be used in the initialization of the eieio \
                     packet (if any)
        :type data: bytearray or None
        :return: None
        :rtype: None
        """
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
        """
        Insert a new key into the eieio packet

        :param key: key to insert
        :type key: 16- or 32- bit unsigned int
        :return: None
        :rtype: None
        """
        self._message.write_data(key)

    def _insert_key_and_payload(self, key, payload):
        """
        Insert a new couple key, payload into the eieio packet

        :param key: key to insert
        :type key: 16- or 32- bit unsigned int
        :param payload: payload to insert associated with the specified key
        :type payload: 16- or 32- bit unsigned int
        :return: None
        :rtype: None
        """
        self._message.write_data(key, payload)

    def get_available_count(self):
        """
        Returns the number of available entries in the eieio packet

        :return: number of available entries in the packet
        :rtype: unsigned int
        """
        available_payload_space = (spinnman_constants.UDP_MESSAGE_MAX_SIZE -
                                   self._length)
        max_float = math.floor(available_payload_space / self._element_size)
        max_count = int(max_float)
        return max_count

    def get_max_count(self):
        """
        Returns the maximum number of entries that a type of eieio packet type

        :return: maximum number of entries that a type of eieio packet type
        can have
        """
        available_payload_space = (spinnman_constants.UDP_MESSAGE_MAX_SIZE -
                                   self._base_size)
        max_float = math.floor(available_payload_space / self._element_size)
        max_count = int(max_float)
        return max_count

    def get_next_element(self):
        """
        Returns the next element in the eieio packet. Depending on the type \
        of packet, the element may include only a key or a couple key, payload

        :return: key, [payload]
        :rtype: unsigned int, [unsigned int]
        """
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

    @staticmethod
    def get_min_length(type_param, tag_param=0, prefix_param=None,
                       payload_base=None, prefix_type=None, is_time=False):
        length = 2  # header size

        if prefix_param is not None:
            length += 2

        if payload_base is not None:
            if type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT \
                    or type_param == EIEIOTypeParam.KEY_16_BIT:
                length += 2
            else:
                length += 4

        if type_param == EIEIOTypeParam.KEY_16_BIT:
            length += 2
        elif type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT:
            length += 4
        elif type_param == EIEIOTypeParam.KEY_32_BIT:
            length += 4
        elif type_param == EIEIOTypeParam.KEY_PAYLOAD_32_BIT:
            length += 8
        else:
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "variable type_param", "unknown type")

        return length

    @staticmethod
    @abstractmethod
    def get_min_packet_length():
        pass

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


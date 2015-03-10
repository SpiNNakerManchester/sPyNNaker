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
        :type payload_base: 16- or 32-bit value, depending on the packet type
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
        """
        Returns the minimum eieio data packet length in bytes, given the \
        configuration of the packet. The minimum length includes one element, \
        whether it consists of a key or a couple key, payload. The function \
        parameters are compatible with the init function call.

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
        :type payload_base: 16- or 32-bit value, depending on the packet type
        :param prefix_type: determines if the prefix_param value has to be \
                            applied on the upper or lower part of the \
                            multicast routing key
        :type prefix_type: spinnman.spinnman.messages.eieio.eieio_prefix_type
        :param is_time: determines if the payload represents a timestamp
        :type is_time: bool
        :return: The minimum size in bytes of the packet with the specified \
                 configuration
        :rtype: unsigned int
        """
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
        """
        Returns the minimum packet length in bytes for each specific type of \
        eieio packet. The function is implemented in each of the inheriting \
        class and references the spynnaker.pyNN.buffer_management.\
        abstract_eieio_packets.abstract_eieio_data_packet.\
        AbstractEIEIODataPacket#get_min_length function

        :return: The minimum size in bytes of the packet
        :rtype: unsigned int
        """
        pass

    @property
    def length(self):
        """
        Returns the current length of the packet in bytes

        :return: The current length of the packet in bytes
        :rtype: unsigned int
        """
        return self._length

    @property
    def element_size(self):
        """
        Returns the size in bytes of each element in the packet  (including \
        payload, if present)

        :return: the size in bytes of each element in the packet \
        (including payload, if present)
        :rtype: unsigned int
        """
        return self._element_size

    @property
    def key_size(self):
        """
        Returns the size in bytes of the key format used in the packet

        :return: the size in bytes of the key used in the packet
        :rtype: unsigned int
        """
        return self._key_size

    @property
    def header_size(self):
        """
        Returns the size of the header in bytes

        :return: the size of the header in bytes
        :rtype: unsigned int
        """
        return self._base_size

    def get_eieio_message_as_byte_array(self):
        """
        Returns the entire eieio packet as a bytearray string, including the \
        header, keys and payload (if present), as specified by the eieio \
        standard

        :return: The eieio packet as a bytearray string
        :rtype: bytearray
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
        """
        Returns the packet type, 16- or 32-bit, with or without payload.

        :return: type of packet: 16- or 32-bit events with or without payload
        :rtype: spinnman.messages.eieio.eieio_type_param.EIEIOTypeParam
        """
        return self._header.prefix_param

    @property
    def payload_base(self):
        """
        Returns the base value to be used in the construction of the payload \
        to the event to be multicasted

        :return: base value to be used in the construction of the payload to \
                 the event to be multicasted
        :rtype: 16- or 32-bit unsigned value, depending on the packet type
        """
        return self._header.payload_base

    @property
    def prefix_type(self):
        """
        Returns the configuration be which describes if the key prefix has to \
        be applied to the upper or lower part of the multicast routing key

        :return: determines if the prefix_param value has to be applied on the \
                 upper or lower part of the multicast routing key
        :rtype: spinnman.spinnman.messages.eieio.eieio_prefix_type
        """
        return self._header.prefix_type

    @property
    def is_time(self):
        """
        Returns true if the payload of each key contained in the eieio packet \
        represents a timestamp

        :return: Boolean representing if the payload of each key contained in \
                 the eieio packet represents a timestamp
        :rtype: bool
        """
        return self._header.is_time

    # user queries
    @property
    def has_payload(self):
        """
        Returns true if each key has a payload associated (including \
        timestamp), whether constant or specific for each key

        :return: if each key in the packet has a payload associated
        :rtype: bool
        """
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
        """
        Returns true if a payload prefix has been defined for the packet

        :return: if a payload prefix has been defined for the packet
        :rtype: bool
        """
        if self.payload_base is not None:
            return False
        else:
            return True

    @property
    def has_fixed_timestamp(self):
        """
        Returns true if the packet has been defined to contain timestamps and \
        a payload prefix, and each key does not have a payload associated

        :return: if the packet includes a fixed timestamp for all the keys in \
                 the packet
        :rtype: bool
        """
        if self.is_time and self.has_payload_prefix:
            if (self._header.type_param == EIEIOTypeParam.KEY_16_BIT or
                    self._header.type_param == EIEIOTypeParam.KEY_32_BIT):
                return True
            else:
                return False
        else:
            return False

    @property
    def has_key_prefix(self):
        """
        Returns true if a key prefix has been defined for the packet

        :return: if a key prefix has been defined for the packet
        :rtype: bool
        """
        if self.key_prefix is not None:
            return False
        else:
            return True

    @property
    def is_timed(self):
        """
        Returns true if the payload associated to each key represents \
        a timestamp

        :return: if the payload associated to each key represents a timestamp
        :rtype: bool
        """
        return self.is_time

    @property
    def payload_prefix(self):
        """
        Returns true if a payload prefix has been defined for the packet

        :return: if a payload prefix has been defined for the packet
        :rtype: bool
        """
        if self.has_payload_prefix:
            return self.payload_base
        else:
            return None

    @property
    def timestamp(self):
        """
        Returns the timestamp in case the packet has a fixed timestamp for all\
        the keys, or None

        :return: timestamp associated with keys in the packet, or None
        :rtype: unsigned int or None
        """
        if self.has_fixed_timestamp:
            return self.payload_prefix
        else:
            return None

    @property
    def key_prefix(self):
        """
        Returns the key prefix in case the packet defines it, or None

        :return: the key prefix in case the packet defines it, or None
        :rtype: 16-bit unsigned int or None
        """
        if self.has_key_prefix:
            return self.prefix_param
        else:
            return None


from abc import abstractmethod
from spinnman import exceptions as spinnman_exceptions
from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_packet import AbstractEIEIOPacket
from spinnman import constants as spinnman_constants

from spynnaker.pyNN.buffer_management.buffer_data_objects.eieio_16bit import \
    eieio_16bit_data_packet, eieio_16bit_lower_key_prefix_data_packet, \
    eieio_16bit_payload_prefix_data_packet, \
    eieio_16bit_payload_prefix_lower_key_prefix_data_packet,\
    eieio_16bit_payload_prefix_upper_key_prefix_data_packet,\
    eieio_16bit_timed_payload_prefix_data_packet,\
    eieio_16bit_timed_payload_prefix_lower_key_prefix_data_packet,\
    eieio_16bit_timed_payload_prefix_upper_key_prefix_data_packet,\
    eieio_16bit_upper_key_prefix_data_packet

from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_16bit_with_payload import eieio_16bit_with_payload_data_packet, \
    eieio_16bit_with_payload_lower_key_prefix_data_packet, \
    eieio_16bit_with_payload_payload_prefix_data_packet, \
    eieio_16bit_with_payload_payload_prefix_lower_key_prefix_data_packet, \
    eieio_16bit_with_payload_payload_prefix_upper_key_prefix_data_packet, \
    eieio_16bit_with_payload_timed_data_packet, \
    eieio_16bit_with_payload_timed_lower_key_prefix_data_packet, \
    eieio_16bit_with_payload_timed_upper_key_prefix_data_packet, \
    eieio_16bit_with_payload_upper_key_prefix_data_packet

from spynnaker.pyNN.buffer_management.buffer_data_objects.eieio_32bit import \
    eieio_32bit_data_packet, \
    eieio_32bit_lower_key_prefix_data_packet, \
    eieio_32bit_payload_prefix_data_packet, \
    eieio_32bit_payload_prefix_lower_key_prefix_data_packet, \
    eieio_32bit_payload_prefix_upper_key_prefix_data_packet, \
    eieio_32bit_timed_payload_prefix_data_packet, \
    eieio_32bit_timed_payload_prefix_lower_key_prefix_data_packet, \
    eieio_32bit_timed_payload_prefix_upper_key_prefix_data_packet, \
    eieio_32bit_upper_key_prefix_data_packet

from spynnaker.pyNN.buffer_management.buffer_data_objects.\
    eieio_32bit_with_payload import eieio_32bit_with_payload_data_packet, \
    eieio_32bit_with_payload_lower_key_prefix_data_packet, \
    eieio_32bit_with_payload_payload_prefix_data_packet, \
    eieio_32bit_with_payload_payload_prefix_lower_key_prefix_data_packet, \
    eieio_32bit_with_payload_payload_prefix_upper_key_prefix_data_packet, \
    eieio_32bit_with_payload_timed_data_packet, \
    eieio_32bit_with_payload_timed_lower_key_prefix_data_packet, \
    eieio_32bit_with_payload_timed_upper_key_prefix_data_packet, \
    eieio_32bit_with_payload_upper_key_prefix_data_packet

import math


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
        max_count = math.floor(available_payload_space / self._element_size)
        return max_count

    def get_max_count(self):
        """
        :return: maximum number of entries that this type of eieio packet type
        can handle
        """
        available_payload_space = (spinnman_constants.UDP_MESSAGE_MAX_SIZE -
                                   self._base_size)
        max_count = math.floor(available_payload_space / self._element_size)
        return max_count

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


    @staticmethod
    def create_packet_from_reader(reader):
        """
        creates a packet of a specific class depending on the format \
        of the incoming data
        :param reader:
        :return:
        """
        # parsed_packet = EIEIOMessage.create_eieio_messages_from(reader)
        # packet_type_number = parsed_packet.eieio_header.type_param * 16
        #
        # if parsed_packet.eieio_header.is_time:
        #     packet_type_number += 8
        #
        # if parsed_packet.eieio_header.payload_base is not None:
        #     packet_type_number += 4
        #
        # if parsed_packet.eieio_header.prefix_type:
        #     packet_type_number += 2
        #
        # if parsed_packet.eieio_header.prefix_param is not None:
        #     packet_type_number += 1
        #
        # packet_types = {
        #     0:  eieio_16bit_data_packet.EIEIO16BitDataPacket(data=parsed_packet.data),
        #     1:  eieio_16bit_lower_key_prefix_data_packet.EIEIO16BitLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     3:  eieio_16bit_upper_key_prefix_data_packet.EIEIO16BitLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     4:  eieio_16bit_payload_prefix_data_packet.EIEIO16BitPayloadPrefixDataPacket(parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     5:  eieio_16bit_payload_prefix_lower_key_prefix_data_packet.EIEIO16BitPayloadPrefixLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     7:  eieio_16bit_payload_prefix_upper_key_prefix_data_packet.EIEIO16BitPayloadPrefixUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     12: eieio_16bit_timed_payload_prefix_data_packet.EIEIO16BitTimedPayloadPrefixDataPacket(parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     13: eieio_16bit_timed_payload_prefix_lower_key_prefix_data_packet.EIEIO16BitTimedPayloadPrefixLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     15: eieio_16bit_timed_payload_prefix_upper_key_prefix_data_packet.EIEIO16BitTimedPayloadPrefixUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     16: eieio_16bit_with_payload_data_packet.EIEIO16BitWithPayloadDataPacket(data=parsed_packet.data),
        #     17: eieio_16bit_with_payload_lower_key_prefix_data_packet.EIEIO16BitWithPayloadLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     19: eieio_16bit_with_payload_upper_key_prefix_data_packet.EIEIO16BitWithPayloadUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     20: eieio_16bit_with_payload_payload_prefix_data_packet.EIEIO16BitWithPayloadPayloadPrefixDataPacket(parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     21: eieio_16bit_with_payload_payload_prefix_lower_key_prefix_data_packet.EIEIO16BitWithPayloadPayloadPrefixLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     23: eieio_16bit_with_payload_payload_prefix_upper_key_prefix_data_packet.EIEIO16BitWithPayloadPayloadPrefixUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     24: eieio_16bit_with_payload_timed_data_packet.EIEIO16BitWithPayloadTimedDataPacket(data=parsed_packet.data),
        #     25: eieio_16bit_with_payload_timed_lower_key_prefix_data_packet.EIEIO16BitWithPayloadTimedLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     27: eieio_16bit_with_payload_timed_upper_key_prefix_data_packet.EIEIO16BitWithPayloadTimedUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     32: eieio_32bit_data_packet.EIEIO32BitDataPacket(data=parsed_packet.data),
        #     33: eieio_32bit_lower_key_prefix_data_packet.EIEIO32BitLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     35: eieio_32bit_upper_key_prefix_data_packet.EIEIO32BitUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     36: eieio_32bit_payload_prefix_data_packet.EIEIO32BitPayloadPrefixDataPacket(parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     37: eieio_32bit_payload_prefix_lower_key_prefix_data_packet.EIEIO32BitPayloadPrefixLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     39: eieio_32bit_payload_prefix_upper_key_prefix_data_packet.EIEIO32BitPayloadPrefixUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     44: eieio_32bit_timed_payload_prefix_data_packet.EIEIO32BitTimedPayloadPrefixDataPacket(parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     45: eieio_32bit_timed_payload_prefix_lower_key_prefix_data_packet.EIEIO32BitTimedPayloadPrefixLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     47: eieio_32bit_timed_payload_prefix_upper_key_prefix_data_packet.EIEIO32BitTimedPayloadPrefixUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     48: eieio_32bit_with_payload_data_packet.EIEIO32BitWithPayloadDataPacket(data=parsed_packet.data),
        #     49: eieio_32bit_with_payload_lower_key_prefix_data_packet.EIEIO32BitWithPayloadLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     51: eieio_32bit_with_payload_upper_key_prefix_data_packet.EIEIO32BitWithPayloadUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     52: eieio_32bit_with_payload_payload_prefix_data_packet.EIEIO32BitWithPayloadPayloadPrefixDataPacket(parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     53: eieio_32bit_with_payload_payload_prefix_lower_key_prefix_data_packet.EIEIO32BitWithPayloadPayloadPrefixLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     55: eieio_32bit_with_payload_payload_prefix_upper_key_prefix_data_packet.EIEIO32BitWithPayloadPayloadPrefixUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, parsed_packet.eieio_header.payload_base, data=parsed_packet.data),
        #     56: eieio_32bit_with_payload_timed_data_packet.EIEIO32BitWithPayloadTimedDataPacket(data=parsed_packet.data),
        #     57: eieio_32bit_with_payload_timed_lower_key_prefix_data_packet.EIEIO32BitWithPayloadTimedLowerKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     59: eieio_32bit_with_payload_timed_upper_key_prefix_data_packet.EIEIO32BitWithPayloadTimedUpperKeyPrefixDataPacket(parsed_packet.eieio_header.prefix_param, data=parsed_packet.data),
        #     }
        #
        # if packet_type_number not in packet_types:
        #     raise
        # else:
        #     packet_types[packet_type_number]
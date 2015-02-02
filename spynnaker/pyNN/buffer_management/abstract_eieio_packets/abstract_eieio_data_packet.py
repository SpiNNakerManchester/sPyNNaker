from abc import abstractmethod
from spinnman import exceptions as spinnman_exceptions
from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_packet import AbstractEIEIOPacket
from spinnman import constants as spinnman_constants

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

    @abstractmethod
    def get_eieio_message_as_byte_array(self):
        """
        returns the eieio packet as a bytearray string
        """

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
        pass
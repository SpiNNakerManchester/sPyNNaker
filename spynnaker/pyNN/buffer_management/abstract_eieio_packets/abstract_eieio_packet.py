from abc import abstractmethod
from spinnman import exceptions as spinnman_exceptions
from spinnman import constants as spinnman_constants
from spinnman.data.little_endian_byte_array_byte_reader import \
    LittleEndianByteArrayByteReader
from spinnman.messages.eieio.eieio_header import EIEIOHeader
from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam

from spynnaker.pyNN.buffer_management.buffer_data_objects import \
    eieio_with_payload_data_packet, eieio_without_payload_data_packet

from spynnaker.pyNN.buffer_management.command_objects.eieio_command_packet \
    import EIEIOCommandPacket

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

from spynnaker.pyNN.buffer_management.command_objects import \
    event_stop_request,\
    padding_request,\
    spinnaker_request_buffers,\
    spinnaker_request_read_data,\
    host_send_sequenced_data,\
    host_data_read,\
    start_requests,\
    stop_requests


class AbstractEIEIOPacket():

    def __init__(self):
        pass

    @abstractmethod
    def get_eieio_message_as_byte_array(self):
        """
        all the eieio data packet classes require a method to convert the
        packet to a bytearray
        """

    @staticmethod
    def create_class_from_reader(reader):
        """
        Interprets the packet received and creates the appropriate class

        :param reader:
        :return:
        """
        byte1 = reader.read_byte()
        byte2 = reader.read_byte()
        header_value = byte2 << 8 | byte1
        if header_value & 0xC000 == 0x4000:  # is a command packet
            return AbstractEIEIOPacket._create_command_from_reader(
                header_value, reader)
        else:  # is data packet
            return AbstractEIEIOPacket._create_data_from_reader(
                header_value, reader)

    @staticmethod
    def create_data_from_reader(reader):
        byte1 = reader.read_byte()
        byte2 = reader.read_byte()
        header_value = byte2 << 8 | byte1

        if header_value & 0xC000 == 0x4000:
            raise  # this is a command packet rather than a data packet
            # Unable to parse here
        else:
            return AbstractEIEIOPacket._create_data_from_reader(
                header_value, reader)

    @staticmethod
    def create_command_from_reader(reader):
        byte1 = reader.read_byte()
        byte2 = reader.read_byte()
        header_value = byte2 << 8 | byte1

        if header_value & 0xC000 != 0x4000:
            raise  # this is a command packet rather than a data packet
            # Unable to parse here
        else:
            return AbstractEIEIOPacket._create_command_from_reader(
                header_value, reader)

    @staticmethod
    def _create_data_from_reader(header_value, reader):
        """
        creates a packet of a specific class depending on the format \
        of the incoming data
        :param reader:
        :return:
        """
        parsed_packet_header = AbstractEIEIOPacket.\
            create_data_header_from_reader(header_value, reader)
        parsed_packet = AbstractEIEIOPacket.create_data_message_from_reader(
            parsed_packet_header, reader)

        packet_type_number = parsed_packet.eieio_header.type_param * 16

        if parsed_packet.eieio_header.is_time:
            packet_type_number += 8

        if parsed_packet.eieio_header.payload_base is not None:
            packet_type_number += 4

        if parsed_packet.eieio_header.prefix_type.value == 1:
            packet_type_number += 2

        if parsed_packet.eieio_header.prefix_param is not None:
            packet_type_number += 1

        if packet_type_number == 0:
            packet = eieio_16bit_data_packet.\
                EIEIO16BitDataPacket(data=parsed_packet.data)
        elif packet_type_number == 1:
            packet = eieio_16bit_lower_key_prefix_data_packet.\
                EIEIO16BitLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 3:
            packet = eieio_16bit_upper_key_prefix_data_packet.\
                EIEIO16BitLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 4:
            packet = eieio_16bit_payload_prefix_data_packet.\
                EIEIO16BitPayloadPrefixDataPacket(
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 5:
            packet = eieio_16bit_payload_prefix_lower_key_prefix_data_packet.\
                EIEIO16BitPayloadPrefixLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 7:
            packet = eieio_16bit_payload_prefix_upper_key_prefix_data_packet.\
                EIEIO16BitPayloadPrefixUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 12:
            packet = eieio_16bit_timed_payload_prefix_data_packet.\
                EIEIO16BitTimedPayloadPrefixDataPacket(
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 13:
            packet = eieio_16bit_timed_payload_prefix_lower_key_prefix_data_packet.\
                EIEIO16BitTimedPayloadPrefixLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 15:
            packet = eieio_16bit_timed_payload_prefix_upper_key_prefix_data_packet.\
                EIEIO16BitTimedPayloadPrefixUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 16:
            packet = eieio_16bit_with_payload_data_packet.\
                EIEIO16BitWithPayloadDataPacket(
                    data=parsed_packet.data)
        elif packet_type_number == 17:
            packet = eieio_16bit_with_payload_lower_key_prefix_data_packet.\
                EIEIO16BitWithPayloadLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 19:
            packet = eieio_16bit_with_payload_upper_key_prefix_data_packet.\
                EIEIO16BitWithPayloadUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 20:
            packet = eieio_16bit_with_payload_payload_prefix_data_packet.\
                EIEIO16BitWithPayloadPayloadPrefixDataPacket(
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 21:
            packet = eieio_16bit_with_payload_payload_prefix_lower_key_prefix_data_packet.\
                EIEIO16BitWithPayloadPayloadPrefixLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 23:
            packet = eieio_16bit_with_payload_payload_prefix_upper_key_prefix_data_packet.\
                EIEIO16BitWithPayloadPayloadPrefixUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 24:
            packet = eieio_16bit_with_payload_timed_data_packet.\
                EIEIO16BitWithPayloadTimedDataPacket(
                    data=parsed_packet.data)
        elif packet_type_number == 25:
            packet = eieio_16bit_with_payload_timed_lower_key_prefix_data_packet.\
                EIEIO16BitWithPayloadTimedLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 27:
            packet = eieio_16bit_with_payload_timed_upper_key_prefix_data_packet.\
                EIEIO16BitWithPayloadTimedUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 32:
            packet = eieio_32bit_data_packet.\
                EIEIO32BitDataPacket(data=parsed_packet.data)
        elif packet_type_number == 33:
            packet = eieio_32bit_lower_key_prefix_data_packet.\
                EIEIO32BitLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 35:
            packet = eieio_32bit_upper_key_prefix_data_packet.\
                EIEIO32BitUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 36:
            packet = eieio_32bit_payload_prefix_data_packet.\
                EIEIO32BitPayloadPrefixDataPacket(
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 37:
            packet = eieio_32bit_payload_prefix_lower_key_prefix_data_packet.\
                EIEIO32BitPayloadPrefixLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 39:
            packet = eieio_32bit_payload_prefix_upper_key_prefix_data_packet.\
                EIEIO32BitPayloadPrefixUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 44:
            packet = eieio_32bit_timed_payload_prefix_data_packet.\
                EIEIO32BitTimedPayloadPrefixDataPacket(
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 45:
            packet = eieio_32bit_timed_payload_prefix_lower_key_prefix_data_packet.\
                EIEIO32BitTimedPayloadPrefixLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 47:
            packet = eieio_32bit_timed_payload_prefix_upper_key_prefix_data_packet.\
                EIEIO32BitTimedPayloadPrefixUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 48:
            packet = eieio_32bit_with_payload_data_packet.\
                EIEIO32BitWithPayloadDataPacket(data=parsed_packet.data)
        elif packet_type_number == 49:
            packet = eieio_32bit_with_payload_lower_key_prefix_data_packet.\
                EIEIO32BitWithPayloadLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 51:
            packet = eieio_32bit_with_payload_upper_key_prefix_data_packet.\
                EIEIO32BitWithPayloadUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 52:
            packet = eieio_32bit_with_payload_payload_prefix_data_packet.\
                EIEIO32BitWithPayloadPayloadPrefixDataPacket(
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 53:
            packet = eieio_32bit_with_payload_payload_prefix_lower_key_prefix_data_packet.\
                EIEIO32BitWithPayloadPayloadPrefixLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 55:
            packet = eieio_32bit_with_payload_payload_prefix_upper_key_prefix_data_packet.\
                EIEIO32BitWithPayloadPayloadPrefixUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    parsed_packet.eieio_header.payload_base,
                    data=parsed_packet.data)
        elif packet_type_number == 56:
            packet = eieio_32bit_with_payload_timed_data_packet.\
                EIEIO32BitWithPayloadTimedDataPacket(
                    data=parsed_packet.data)
        elif packet_type_number == 57:
            packet = eieio_32bit_with_payload_timed_lower_key_prefix_data_packet.\
                EIEIO32BitWithPayloadTimedLowerKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        elif packet_type_number == 59:
            packet = eieio_32bit_with_payload_timed_upper_key_prefix_data_packet.\
                EIEIO32BitWithPayloadTimedUpperKeyPrefixDataPacket(
                    parsed_packet.eieio_header.prefix_param,
                    data=parsed_packet.data)
        else:
            if (parsed_packet.eieio_header.type_param ==
                    EIEIOTypeParam.KEY_16_BIT or
                    parsed_packet.eieio_header.type_param ==
                    EIEIOTypeParam.KEY_32_BIT):
                packet = eieio_without_payload_data_packet.\
                    EIEIOWithoutPayloadDataPacket(
                        parsed_packet.eieio_header.type_param,
                        prefix_param=parsed_packet.eieio_header.prefix_param,
                        payload_base=parsed_packet.eieio_header.payload_base,
                        prefix_type=parsed_packet.eieio_header.prefix_type,
                        is_time=parsed_packet.eieio_header.is_time,
                        data=parsed_packet.data)
            else:
                packet = eieio_with_payload_data_packet.\
                    EIEIOWithPayloadDataPacket(
                        parsed_packet.eieio_header.type_param,
                        prefix_param=parsed_packet.eieio_header.prefix_param,
                        payload_base=parsed_packet.eieio_header.payload_base,
                        prefix_type=parsed_packet.eieio_header.prefix_type,
                        is_time=parsed_packet.eieio_header.is_time,
                        data=parsed_packet.data)

        return packet

    @staticmethod
    def create_data_header_from_reader(header_value, byte_reader):
        """ Read an eieio data header from a byte_reader, from which the
         initial two bytes have already been read to identify a command or a
         data packet

        :param byte_reader: The reader to read the data from
        :type byte_reader:\
                    :py:class:`spinnman.data.abstract_byte_reader.AbstractByteReader`
        :return: a eieio header
        :rtype: :py:class:`spinnman.data.eieio.eieio_header.EIEIOHeader`
        :raise spinnman.exceptions.SpinnmanIOException: If there is an error\
                    reading from the reader
        :raise spinnman.exceptions.SpinnmanInvalidPacketException: If there\
                    are too few bytes to read the header
        :raise spinnman.exceptions.SpinnmanInvalidParameterException: If there\
                    is an error setting any of the values
        """
        count = header_value & 0xFF
        header_data = (header_value > 8) & 0xFF
        p = (header_data >> 7) & 1
        f = (header_data >> 6) & 1
        d = (header_data >> 5) & 1
        t = (header_data >> 4) & 1

        message_type = (header_data >> 2) & 3
        tag = header_data & 3
        prefix = None
        if p == 1:
            prefix2 = byte_reader.read_byte()
            prefix1 = byte_reader.read_byte()
            prefix = (prefix1 << 8) | prefix2

        if f != 0:
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "eieio header", "the format param from the received packet is "
                                "invalid")
        if d == 1:
            if message_type == 0 or message_type == 1:  # 16 bits
                d2 = byte_reader.read_byte()
                d1 = byte_reader.read_byte()
                d = (d1 << 8) | d2
            elif message_type == 2 or message_type == 3:  # 32 bits
                d4 = byte_reader.read_byte()
                d3 = byte_reader.read_byte()
                d2 = byte_reader.read_byte()
                d1 = byte_reader.read_byte()
                d = (d1 << 24) | (d2 << 16) | (d3 << 8) | d4
            else:
                raise spinnman_exceptions.SpinnmanInvalidPacketException(
                    "eieio header", "the type param from the received packet "
                                    "is invalid")

        if message_type == 0:
            message_type = EIEIOTypeParam.KEY_16_BIT
        elif message_type == 1:
            message_type = EIEIOTypeParam.KEY_PAYLOAD_16_BIT
        elif message_type == 2:
            message_type = EIEIOTypeParam.KEY_32_BIT
        elif message_type == 3:
            message_type = EIEIOTypeParam.KEY_PAYLOAD_32_BIT
        else:
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "eieio header", "the type param from the received packet is "
                                "invalid")

        header = EIEIOHeader(
            type_param=message_type, tag_param=tag, prefix_param=prefix,
            payload_base=d, prefix_type=f, is_time=bool(t))

        header.set_count_param(count)

        return header

    @staticmethod
    def create_data_message_from_reader(eieio_header, buffer_data):
        """this method takes a collection of buffers in the form of a single
        byte array, a fully formed eieio header and a position in the byte array
         and interprets them as a fully formed eieio message

        :param buffer_data: the byte array data
        :type buffer_data: LittleEndianByteArrayByteReader
        :param eieio_header: the eieio header which informs the method how to
                             interprets the buffer data
        :type eieio_header: EIEIOHeader
        :rtype: EIEIOMessage
        :return: a EIEIOMessage
        """
        each_piece_of_data = 0
        if eieio_header.type_param == EIEIOTypeParam.KEY_16_BIT:
            each_piece_of_data += 2
        elif eieio_header.type_param == EIEIOTypeParam.KEY_32_BIT:
            each_piece_of_data += 4
        elif eieio_header.type_param == EIEIOTypeParam.KEY_PAYLOAD_16_BIT:
            each_piece_of_data += 4
        elif eieio_header.type_param == EIEIOTypeParam.KEY_PAYLOAD_32_BIT:
            each_piece_of_data += 8
        else:
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                "eieio_header.type_param", "invalid")

        data_to_read = eieio_header.count_param * each_piece_of_data

        data = buffer_data.read_bytes(data_to_read)
        return EIEIOMessage(eieio_header, data)

    @staticmethod
    def _create_command_from_reader(header_value, byte_reader):
        """ Read an eieio command header from a byte reader, from which the
         initial two bytes have already been read to identify a command or a
         data packet

        :param byte1:
        :param byte2:
        :param byte_reader:
        :return:
        """
        command_number = header_value & 0x3FFF

        # Fill in buffer area with padding
        if (command_number ==
                spinnman_constants.EIEIO_COMMAND_IDS.EVENT_PADDING.value):
            return padding_request.PaddingRequest.\
                create_command_from_reader(byte_reader)

        # End of all buffers, stop execution
        elif (command_number ==
                spinnman_constants.EIEIO_COMMAND_IDS.EVENT_STOP.value):
            return event_stop_request.EventStopRequest.\
                create_command_from_reader(byte_reader)

        # Stop complaining that there is sdram free space for buffers
        elif (command_number == spinnman_constants.EIEIO_COMMAND_IDS.
                STOP_SENDING_REQUESTS.value):
            return stop_requests.StopRequests.\
                create_command_from_reader(byte_reader)

        # Start complaining that there is sdram free space for buffers
        elif (command_number == spinnman_constants.EIEIO_COMMAND_IDS.
                START_SENDING_REQUESTS.value):
            return start_requests.StartRequests.\
                create_command_from_reader(byte_reader)

        # Spinnaker requesting new buffers for spike source population
        elif (command_number == spinnman_constants.EIEIO_COMMAND_IDS.
                SPINNAKER_REQUEST_BUFFERS.value):
            return spinnaker_request_buffers.SpinnakerRequestBuffers.\
                create_command_from_reader(byte_reader)

        # Buffers being sent from host to SpiNNaker
        elif (command_number == spinnman_constants.EIEIO_COMMAND_IDS.
                HOST_SEND_SEQUENCED_DATA.value):
            return host_send_sequenced_data.HostSendSequencedData.\
                create_command_from_reader(byte_reader)

        # Buffers available to be read from a buffered out vertex
        elif (command_number == spinnman_constants.EIEIO_COMMAND_IDS.
                SPINNAKER_REQUEST_READ_DATA.value):
            return spinnaker_request_read_data.SpinnakerRequestReadData.\
                create_command_from_reader(byte_reader)

        # Host confirming data being read form SpiNNaker memory
        elif (command_number ==
                spinnman_constants.EIEIO_COMMAND_IDS.HOST_DATA_READ.value):
            return host_data_read.HostDataRead.\
                create_command_from_reader(byte_reader)

        # in all the other cases, parse it as a command packet with payload
        else:
            return EIEIOCommandPacket.create_command_packet_from_reader(
                command_number, byte_reader)

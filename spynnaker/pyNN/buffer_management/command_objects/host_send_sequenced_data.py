from spinnman.data.little_endian_byte_array_byte_reader import \
    LittleEndianByteArrayByteReader
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_packet import AbstractEIEIOPacket
from spynnaker.pyNN.buffer_management.command_objects.eieio_command_packet \
    import EIEIOCommandPacket
from spynnaker.pyNN import exceptions

from spinnman import constants as spinnman_constants


class HostSendSequencedData(EIEIOCommandPacket):

    def __init__(self, eieio_data_packet, region_id, sequence_no):
        if not isinstance(eieio_data_packet, (bytearray, AbstractEIEIOPacket)):
            raise exceptions.InvalidParameterType(
                "Parameter eieio_data_packet is of an unknown type")
        if isinstance(eieio_data_packet, AbstractEIEIOPacket):
            eieio_data_packet = \
                eieio_data_packet.get_eieio_message_as_byte_array()
        self._sequence_no = sequence_no
        self._region_id = region_id
        self._data = bytearray()
        self._data.append(region_id)
        self._data.append(sequence_no)
        self._data.extend(eieio_data_packet)
        EIEIOCommandPacket.__init__(
            self, spinnman_constants.EIEIO_COMMAND_IDS.HOST_SEND_SEQUENCED_DATA.value,
            self._data)

    @property
    def region_id(self):
        return self._region_id

    @property
    def sequence_no(self):
        return self._sequence_no

    def is_command_packet(self):
        return True

    def get_eieio_message_as_byte_array(self):
        return EIEIOCommandPacket.get_eieio_message_as_byte_array(self)

    @staticmethod
    def create_command_from_reader(byte_reader):
        region_id = (byte_reader.read_byte()) & 0x0F
        sequence_no = byte_reader.read_byte()
        data = byte_reader.read_bytes()
        packet = HostSendSequencedData(data, region_id, sequence_no)
        return packet

    @staticmethod
    def get_header_size():
        return 4
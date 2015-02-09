from spynnaker.pyNN.buffer_management.command_objects.eieio_command_packet \
    import EIEIOCommandPacket
from spynnaker.pyNN import exceptions

from spinnman.messages.eieio.eieio_message import EIEIOMessage
from spinnman import constants as spinnman_constants


class HostDataRead(EIEIOCommandPacket):

    def __init__(self, region_id, sequence_no, space_read):
        self._region_id = region_id
        self._sequence_no = sequence_no
        self._space_read = space_read

        self._data = bytearray()
        self._data.append(region_id)
        self._data.append(sequence_no)
        space_byte1 = space_read & 0xFF
        space_byte2 = (space_read >> 8) & 0xFF
        space_byte3 = (space_read >> 16) & 0xFF
        space_byte4 = (space_read >> 24) & 0xFF
        self._data.append(space_byte1)
        self._data.append(space_byte2)
        self._data.append(space_byte3)
        self._data.append(space_byte4)
        EIEIOCommandPacket.__init__(
            self, spinnman_constants.EIEIO_COMMAND_IDS.NEW_BUFFERS.value,
            self._data)

    @property
    def sequence_no(self):
        return self._sequence_no

    @property
    def region_id(self):
        return self._region_id

    @property
    def space_read(self):
        return self._space_read

    def is_command_packet(self):
        return True

    def get_eieio_message_as_byte_array(self):
        return EIEIOCommandPacket.get_eieio_message_as_byte_array(self)

    @staticmethod
    def create_command_from_reader(byte_reader):
        region_id = (byte_reader.read_byte()) & 0xF
        sequence_no = byte_reader.read_byte()
        space_read = byte_reader.read_int()
        packet = HostDataRead(region_id, sequence_no, space_read)
        return packet

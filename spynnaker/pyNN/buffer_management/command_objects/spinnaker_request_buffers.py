from spynnaker.pyNN.buffer_management.command_objects.eieio_command_packet \
    import EIEIOCommandPacket

from spinnman.data.little_endian_byte_array_byte_reader import \
    LittleEndianByteArrayByteReader
from spinnman import constants as spinnman_constants


class SpinnakerRequestBuffers(EIEIOCommandPacket):

    def __init__(self, x, y, p, region_id, sequence_no, space_available):
        self._x = x
        self._y = y
        self._p = p
        self._region_id = region_id
        self._sequence_no = sequence_no
        self._space_available = space_available

        self._data = bytearray()
        self._data.append(x)
        self._data.append(y)
        processor = (self._p << 3)
        self._data.append(processor)
        self._data.append(0)
        self._data.append(region_id)
        self._data.append(sequence_no)
        space_byte1 = space_available & 0xFF
        space_byte2 = (space_available >> 8) & 0xFF
        space_byte3 = (space_available >> 16) & 0xFF
        space_byte4 = (space_available >> 24) & 0xFF
        self._data.append(space_byte1)
        self._data.append(space_byte2)
        self._data.append(space_byte3)
        self._data.append(space_byte4)

        cmd = spinnman_constants.EIEIO_COMMAND_IDS.SPINNAKER_REQUEST_BUFFERS.\
            value
        EIEIOCommandPacket.__init__(self, cmd, self._data)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def p(self):
        return self._p

    @property
    def region_id(self):
        return self._region_id

    @property
    def sequence_no(self):
        return self._sequence_no

    @property
    def space_available(self):
        return self._space_available

    @property
    def data(self):
        return self._data

    def is_command_packet(self):
        return True

    def get_eieio_message_as_byte_array(self):
        return EIEIOCommandPacket.get_eieio_message_as_byte_array(self)

    @staticmethod
    def create_command_from_reader(byte_reader):
        x = byte_reader.read_byte()
        y = byte_reader.read_byte()
        processor = byte_reader.read_byte()
        p = (processor >> 3) & 0x1F
        _ = byte_reader.read_byte()
        region_id = byte_reader.read_byte() & 0xF
        sequence_no = byte_reader.read_byte()
        space = byte_reader.read_int()
        return SpinnakerRequestBuffers(x, y, p, region_id, sequence_no, space)

    @staticmethod
    def get_header_size():
        return 8
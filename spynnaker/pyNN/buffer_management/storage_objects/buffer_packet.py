import math


class BufferPacket(object):
    """ packet thats stored within a eieio command message when its a buffer
        based eieio command message.

    """

    def __init__(self, chip_x, chip_y, chip_p, command, region_id,
                 count, last_timer_tic):
        self._chip_x = chip_x
        self._chip_y = chip_y
        self._chip_p = chip_p
        self._command = command
        self._region_id = region_id
        self._count = count
        self._seqeunce_no = last_timer_tic

    @property
    def chip_x(self):
        return self._chip_x

    @property
    def chip_y(self):
        return self._chip_y

    @property
    def chip_p(self):
        return self._chip_p

    @property
    def command(self):
        return self._command

    @property
    def region_id(self):
        return self._region_id

    @property
    def count(self):
        return self._count

    @property
    def sequence_no(self):
        return self._seqeunce_no

    @staticmethod
    def build_buffer_packet_from_byte_array_reader(reader):
        """ converts a byte array reader into a buffered packet. the format of
        the buffered packet as currently defined is:

              25                         55
        ======H============  ============D===========================
        |[8][8][5][4]      | |[11]     [4]         [8]        [32]   |
        |[x][y][p][command]| |[spare] [region id]  [seq_no]   [count]|


        :param reader: the reader for which the buffered packet is being read
        :type reader: imp of abstract byte reader
        :return: a buffered Packet
        :rtype: sPyNNaker.pyNN.buffer_management.buffered_packet.BufferedPacket
        :raises EOF: if the reader doesnt have enough data to create a buffered
        packet
        """
        chip_x = reader.read_byte()
        chip_y = reader.read_byte()
        p_and_most_of_command = reader.read_byte()
        chip_p = p_and_most_of_command >> 3
        most_of_command = (p_and_most_of_command & math.pow(2, 3))
        last_of_command_command_id_region_id = reader.read_byte()
        last_of_command = (last_of_command_command_id_region_id >> 7)
        command = (most_of_command << 3) + last_of_command
        region_id = (last_of_command_command_id_region_id & math.pow(2, 4))
        last_timer_tic = reader.read_int()
        count = reader.read_int()
        return BufferPacket(chip_x, chip_y, chip_p, command, region_id, count,
                            last_timer_tic)

from spynnaker.pyNN.buffer_management.command_objects.eieio_command_packet import EIEIOCommandPacket

from spinnman import constants as spinnman_constants


class StopRequests(EIEIOCommandPacket):

    def __init__(self):
        EIEIOCommandPacket.__init__(
            self,
            spinnman_constants.EIEIO_COMMAND_IDS.STOP_SENDING_REQUESTS.value)

    def is_command_packet(self):
        return True

    @staticmethod
    def create_command_from_reader(_):
        packet = StopRequests()
        return packet

    @staticmethod
    def get_header_size():
        return 2
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
    def create_command_from_reader(byte_reader):
        packet = StopRequests()
        return packet
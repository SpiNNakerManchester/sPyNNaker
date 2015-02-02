from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_command_packet import AbstractEIEIOCommandPacket

from spinnman import constants as spinnman_constants


class StartRequestsRequest(AbstractEIEIOCommandPacket):

    def __init__(self):
        AbstractEIEIOCommandPacket.__init__(
            self,
            spinnman_constants.EIEIO_COMMAND_IDS.START_SENDING_REQUESTS.value)

    def is_command_packet(self):
        return True

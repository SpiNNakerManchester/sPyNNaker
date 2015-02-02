from spinnman import constants as spinnman_constants

from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_command_packet import AbstractEIEIOCommandPacket


class EventStopRequest(AbstractEIEIOCommandPacket):

    def __init__(self):
        AbstractEIEIOCommandPacket.__init__(
            self, spinnman_constants.EIEIO_COMMAND_IDS.EVENT_STOP.value)

    def is_command_packet(self):
        return True


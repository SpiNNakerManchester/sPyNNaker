from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractEIEIOPacket():
    """
    This class represent a generic eieio packet used in the communication
    with the SpiNNaker machine
    """

    def __init__(self):
        pass

    @abstractmethod
    def get_eieio_message_as_byte_array(self):
        """
        all the eieio data packet classes require a method to convert the
        packet to a bytearray
        """

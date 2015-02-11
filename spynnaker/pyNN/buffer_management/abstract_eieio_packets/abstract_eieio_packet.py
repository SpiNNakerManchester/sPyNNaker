from abc import abstractmethod


class AbstractEIEIOPacket():

    def __init__(self):
        pass

    @abstractmethod
    def get_eieio_message_as_byte_array(self):
        """
        all the eieio data packet classes require a method to convert the
        packet to a bytearray
        """

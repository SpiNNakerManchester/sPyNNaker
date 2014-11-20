from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractRequest(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_eieio_command_message_as_byte_array(self):
        """ method to force requests to generate command messages in the correct
        format for a sdp message

        :return:
        """

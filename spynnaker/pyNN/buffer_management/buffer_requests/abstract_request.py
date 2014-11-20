from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractRequest(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_eieio_command_message(self):
        """ method to force requests to generate command messages

        :return:
        """

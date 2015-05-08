"""
AbstractModelComponent
"""

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractModelComponent(object):
    """
    AbstractModelComponent which supports the getting of the input magic number
    """

    def __init(self):
        pass

    @abstractmethod
    def get_model_magic_number(self):
        """
        method for getting the magic number
        :return:
        """
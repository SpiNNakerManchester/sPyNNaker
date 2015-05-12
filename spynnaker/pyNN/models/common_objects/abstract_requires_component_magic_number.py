"""
AbstractRequiresComponentMagicNumber
"""
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractRequiresComponentMagicNumber(object):
    """
    class to enfroce a function to retrieve a value for a compoennts magic number
    """

    @abstractmethod
    def get_component_magic_number_identifiers(self):
        """
        returns a iteraable of values that are unque identifiers for bits of a
        compoent or its entire components.
        :return: an iterable of ints each of which represent some component
        which requires a magic number to be checked against
        """


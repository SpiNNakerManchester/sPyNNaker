from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractPopulationSettable(object):
    """ Indicates that some properties of this object can be accessed from\
        the PyNN population set and get methods
    """

    @abstractmethod
    def get_value(self, key):
        """ Get a property
        """

    @abstractmethod
    def set_value(self, key, value):
        """ Set a property

        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """

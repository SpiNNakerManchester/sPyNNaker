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

    @abstractmethod
    def parameters_have_changed(self):
        """ Indicate that one or more parameters have changed.
        Should initially be false.
        :returns: bool"""

    @abstractmethod
    def mark_parameters_unchanged(self):
        """ Mark all parameters as unchanged.
        """

    @abstractmethod
    def update_parameters(self, txrx, vertex_slice, placement):
        """ Write updated parameters to SpiNNaker.
        """
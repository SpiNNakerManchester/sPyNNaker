from spynnaker.pyNN import exceptions
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod

__slots__ = ()


@add_metaclass(AbstractBase)
class AbstractContainsUnits(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_units(self, variable):
        """ get units for a given variable
        
        :param variable: the variable to find units from
        :return: the units as a string.
        """

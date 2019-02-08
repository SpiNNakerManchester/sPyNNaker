from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractContainsUnits(object):

    __slots__ = ()

    @abstractmethod
    def get_units(self, variable):
        """ Get units for a given variable

        :param variable: the variable to find units from
        :return: the units as a string.
        """

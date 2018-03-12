from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.ranged.abstract_list import AbstractList
from spynnaker.pyNN.utilities.ranged.spynakker_ranged_list import \
    SpynakkerRangedList

from .abstract_settable import AbstractSettable


@add_metaclass(AbstractBase)
class AbstractPopulationSettable(AbstractSettable):
    """ Indicates that some properties of this object can be accessed from\
        the PyNN population set and get methods
    """

    __slots__ = ()

    @abstractproperty
    def n_atoms(self):
        """" See ApplicationVertex.n_atoms """

    def get_value_by_selector(self, selector, key):
        """
        Gets the value for a particular key but only for the selected subset
        :param selector: See RangedList.get_value_by_selector as this is just \
            a pass through method
        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """
        old_values = self.get_value(key)
        if isinstance(old_values, AbstractList):
            ranged_list = old_values
        else:
            # Keep all the getting stuff in one place by creating a RangedList
            ranged_list = SpynakkerRangedList(
                size=self.n_atoms, value=old_values)
            # Now that we have created a RangedList why not use it.
            self.set_value(key, ranged_list)
        return ranged_list.get_values(selector)

    def set_value_by_selector(self, selector, key, value):
        """
        Sets the value for a particular key but only for the selected subset
        :param selector: See RangedList.set_value_by_selector as this is just \
            a pass through method
        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """
        old_values = self.get_value(key)
        if isinstance(old_values, AbstractList):
            ranged_list = old_values
        else:
            # Keep all the setting stuff in one place by creating a RangedList
            ranged_list = SpynakkerRangedList(
                size=self.n_atoms, value=old_values)
            self.set_value(key, ranged_list)
        ranged_list.set_value_by_selector(selector, value)

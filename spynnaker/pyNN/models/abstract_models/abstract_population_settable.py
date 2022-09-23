# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.require_subclass import require_subclass
from spinn_utilities.ranged.abstract_list import AbstractList
from pacman.model.graphs.application import ApplicationVertex
from spynnaker.pyNN.utilities.ranged import SpynnakerRangedList
from .abstract_settable import AbstractSettable


@require_subclass(ApplicationVertex)
class AbstractPopulationSettable(AbstractSettable, metaclass=AbstractBase):
    """ Indicates that some properties of this application vertex can be\
        accessed from the PyNN population set and get methods.
    """

    __slots__ = ()

    @abstractproperty
    def n_atoms(self):
        """" See :py:meth:\
            `~pacman.model.graphs.application.ApplicationVertex.n_atoms`
        """

    def get_value_by_selector(self, selector, key):
        """ Gets the value for a particular key but only for the selected\
            subset.

        :param selector: See
            :py:meth:`~spinn_utilities.ranged.RangedList.get_value_by_selector`
            as this is just a pass through method
        :type selector: None or slice or int or list(bool) or list(int)
        :param str key: the name of the parameter to change
        :rtype: list(float or int)
        """
        old_values = self.get_value(key)
        if isinstance(old_values, AbstractList):
            ranged_list = old_values
        else:
            # Keep all the getting stuff in one place by creating a RangedList
            ranged_list = SpynnakerRangedList(
                size=self.n_atoms, value=old_values)
            # Now that we have created a RangedList why not use it.
            self.set_value(key, ranged_list)
        return ranged_list.get_values(selector)

    def set_value_by_selector(self, selector, key, value):
        """ Sets the value for a particular key but only for the selected \
            subset.

        :param selector: See \
            :py:class:`~spinn_utilities.ranged.RangedList`.set_value_by_selector\
            as this is just a pass through method
        :type selector: None or slice or int or list(bool) or list(int)
        :param str key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        :type value: float or int or list(float) or list(int)
        """
        old_values = self.get_value(key)
        if isinstance(old_values, AbstractList):
            ranged_list = old_values
        else:
            # Keep all the setting stuff in one place by creating a RangedList
            ranged_list = SpynnakerRangedList(
                size=self.n_atoms, value=old_values)

        ranged_list.set_value_by_selector(
            selector, value, ranged_list.is_list(value, self.n_atoms))
        self.set_value(key, ranged_list)

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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractSettable(object, metaclass=AbstractBase):
    """ Indicates that some properties of this object can be accessed from\
        the PyNN population set and get methods.
    """

    __slots__ = ()

    @abstractmethod
    def get_value(self, key):
        """ Get a property

        :param str key: the name of the property
        :rtype: Any or float or int or list(float) or list(int)
        """

    @abstractmethod
    def set_value(self, key, value):
        """ Set a property

        :param str key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        :type value: Any or float or int or list(float) or list(int)
        """

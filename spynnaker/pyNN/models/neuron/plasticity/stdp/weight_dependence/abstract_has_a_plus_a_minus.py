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

from spinn_utilities.abstract_base import AbstractBase


class AbstractHasAPlusAMinus(object, metaclass=AbstractBase):
    r""" An object that has :math:`A^+` and :math:`A^-` properties.
    """
    __slots__ = [
        '__a_plus',
        '__a_minus'
    ]

    def __init__(self):
        self.__a_plus = None
        self.__a_minus = None

    def set_a_plus_a_minus(self, a_plus, a_minus):
        """ Set the values of :math:`A^+` and :math:`A^-`.

        :param float a_plus: :math:`A^+`
        :param float a_minus: :math:`A^-`
        """
        self.__a_plus = a_plus
        self.__a_minus = a_minus

    @property
    def A_plus(self):
        """ Settable model parameter: :math:`A^+`

        :rtype: float
        """
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value):
        self.__a_plus = new_value

    @property
    def A_minus(self):
        """ Settable model parameter: :math:`A^-`

        :rtype: float
        """
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value):
        self.__a_minus = new_value

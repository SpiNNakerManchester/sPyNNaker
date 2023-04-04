# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.abstract_base import AbstractBase


class AbstractHasAPlusAMinus(object, metaclass=AbstractBase):
    """
    An object that has :math:`A^+` and :math:`A^-` properties.
    """
    __slots__ = [
        '__a_plus',
        '__a_minus'
    ]

    def __init__(self):
        self.__a_plus = None
        self.__a_minus = None

    def set_a_plus_a_minus(self, a_plus, a_minus):
        """
        Set the values of :math:`A^+` and :math:`A^-`.

        :param float a_plus: :math:`A^+`
        :param float a_minus: :math:`A^-`
        """
        self.__a_plus = a_plus
        self.__a_minus = a_minus

    @property
    def A_plus(self):
        """
        Settable model parameter: :math:`A^+`

        :rtype: float
        """
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value):
        self.__a_plus = new_value

    @property
    def A_minus(self):
        """
        Settable model parameter: :math:`A^-`

        :rtype: float
        """
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value):
        self.__a_minus = new_value

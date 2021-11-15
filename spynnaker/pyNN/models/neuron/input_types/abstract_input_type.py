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
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)


class AbstractInputType(
        AbstractStandardNeuronComponent, metaclass=AbstractBase):
    """ Represents a possible input type for a neuron model (e.g., current).
    """
    __slots__ = ()

    @abstractmethod
    def get_global_weight_scale(self):
        """ Get the global weight scaling value.

        :return: The global weight scaling value
        :rtype: float
        """

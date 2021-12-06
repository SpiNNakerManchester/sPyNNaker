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


class AbstractSynapseType(
        AbstractStandardNeuronComponent, metaclass=AbstractBase):
    """ Represents the synapse types supported.
    """

    __slots__ = ()

    @abstractmethod
    def get_n_synapse_types(self):
        """ Get the number of synapse types supported.

        :return: The number of synapse types supported
        :rtype: int
        """

    @abstractmethod
    def get_synapse_id_by_target(self, target):
        """ Get the ID of a synapse given the name.

        :return: The ID of the synapse
        :rtype: int
        """

    @abstractmethod
    def get_synapse_targets(self):
        """ Get the target names of the synapse type.

        :return: an array of strings
        :rtype: array(str)
        """

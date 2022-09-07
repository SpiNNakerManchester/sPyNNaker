# Copyright (c) 2021-2022 The University of Manchester
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


class AbstractSupportsSignedWeights(object, metaclass=AbstractBase):
    """ A synapse dynamics object that supports signed weights
    """

    @abstractmethod
    def get_positive_synapse_index(self, incoming_projection):
        """ Get the synapse type that positive weights will arrive at

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: int
        """

    @abstractmethod
    def get_negative_synapse_index(self, incoming_projection):
        """ Get the synapse type that negative weights will arrive at

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: int
        """

    @abstractmethod
    def get_maximum_positive_weight(self, incoming_projection):
        """ Get the maximum likely positive weight.
            Note this must be a value >= 0.

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: float
        """

    @abstractmethod
    def get_minimum_negative_weight(self, incoming_projection):
        """ Get the minimum likely negative weight.
            Note this must be a value <= 0.

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: int
        """

    @abstractmethod
    def get_mean_positive_weight(self, incoming_projection):
        """ Get the mean of the positive weights.
            Note this must be a value >= 0.

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: float
        """

    @abstractmethod
    def get_mean_negative_weight(self, incoming_projection):
        """ Get the mean of the negative weights.
            Note this must be a value <= 0.

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: float
        """

    @abstractmethod
    def get_variance_positive_weight(self, incoming_projection):
        """ Get the variance of the positive weights.
            Note this must be a value >= 0.

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: float
        """

    @abstractmethod
    def get_variance_negative_weight(self, incoming_projection):
        """ Get the variance of the negative weights.
            Note this must be a value <= 0.

        :param ~spynnaker.pyNN.models.projection.Projection\
            incoming_projection: The projection targeted
        :rtype: float
        """

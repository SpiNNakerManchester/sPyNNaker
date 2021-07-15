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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractSynapseDynamics(object, metaclass=AbstractBase):
    """ How do the dynamics of a synapse interact with the rest of the model.
    """

    __slots__ = ()

    @abstractmethod
    def merge(self, synapse_dynamics):
        """ Merge with the given synapse_dynamics and return the result, or\
            error if merge is not possible

        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: AbstractSynapseDynamics
        """

    @abstractmethod
    def are_weights_signed(self):
        """ Determines if the weights are signed values

        :rtype: bool
        """

    @abstractmethod
    def get_vertex_executable_suffix(self):
        """ Get the executable suffix for a vertex for this dynamics

        :rtype: str
        """

    @abstractproperty
    def changes_during_run(self):
        """ Determine if the synapses change during a run

        :rtype: bool
        """

    @abstractproperty
    def delay(self):
        """ The delay of connections
        """

    @abstractmethod
    def set_delay(self, delay):
        """ Set the delay
        """

    @abstractproperty
    def weight(self):
        """ The weight of connections
        """

    def get_delay_maximum(self, connector, synapse_info):
        """ Get the maximum delay for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray delays:
        """
        return connector.get_delay_maximum(synapse_info)

    def get_delay_minimum(self, connector, synapse_info):
        """ Get the minimum delay for the synapses. \
            This will support the filtering of the undelayed edge\
            from the graph, but requires fixes in the synaptic manager to \
            happen first before this can be utilised fully.

        :param AbstractConnector connector: connector
        :param ~numpy.ndarray synapse_info: synapse info
        """
        return connector.get_delay_minimum(synapse_info)

    def get_delay_variance(self, connector, delays, synapse_info):
        """ Get the variance in delay for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray delays:
        """
        # pylint: disable=too-many-arguments
        return connector.get_delay_variance(delays, synapse_info)

    def get_weight_mean(self, connector, synapse_info):
        """ Get the mean weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_mean(synapse_info.weights, synapse_info)

    def get_weight_maximum(self, connector, synapse_info):
        """ Get the maximum weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_maximum(synapse_info)

    def get_weight_variance(self, connector, weights, synapse_info):
        """ Get the variance in weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_variance(weights, synapse_info)

    def get_provenance_data(self, pre_population_label, post_population_label):
        """ Get the provenance data from this synapse dynamics object

        :param str pre_population_label:
        :param str post_population_label:
        :rtype:
            iterable(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
        """
        # pylint: disable=unused-argument
        return []

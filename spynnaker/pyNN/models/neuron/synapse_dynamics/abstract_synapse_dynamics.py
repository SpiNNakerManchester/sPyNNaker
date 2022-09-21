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
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH


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
    def weight(self):
        """ The weight of connections
        """

    @abstractproperty
    def delay(self):
        """ The delay of connections
        """

    @abstractmethod
    def set_delay(self, delay):
        """ Set the delay
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
        return connector.get_delay_variance(delays, synapse_info)

    def get_weight_mean(self, connector, synapse_info):
        """ Get the mean weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        return connector.get_weight_mean(synapse_info.weights, synapse_info)

    def get_weight_maximum(self, connector, synapse_info):
        """ Get the maximum weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        return connector.get_weight_maximum(synapse_info)

    def get_weight_variance(self, connector, weights, synapse_info):
        """ Get the variance in weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
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

    def get_synapse_id_by_target(self, target):
        """ Get the index of the synapse type based on the name, or None
            if the name is not found.

        :param str target: The name of the synapse
        :rtype: int or None
        """
        # pylint: disable=unused-argument
        return None

    def get_connected_vertices(self, s_info, source_vertex, target_vertex):
        """ Get the machine vertices that are connected to each other with
            this connector

        :param SynapseInformation s_info:
            The synapse information of the connection
        :param ApplicationVertex source_vertex: The source of the spikes
        :param ApplicationVertex target_vertex: The target of the spikes
        :return: A list of tuples of (target machine vertex, source
        :rtype: list(tuple(MachineVertex, list(AbstractVertex)))
        """
        # By default, just ask the connector
        return s_info.connector.get_connected_vertices(
            s_info, source_vertex, target_vertex)

    @property
    def absolute_max_atoms_per_core(self):
        """ The absolute maximum number of atoms per core supported by this
            synapse dynamics object
        """
        # By default, we can only support the maximum row length per core
        return POP_TABLE_MAX_ROW_LENGTH

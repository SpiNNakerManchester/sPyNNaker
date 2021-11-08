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

import math
import numpy
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractSynapseDynamics(object, metaclass=AbstractBase):
    """ How do the dynamics of a synapse interact with the rest of the model.
    """

    __slots__ = ()

    #: Type model of the basic configuration data of a connector
    NUMPY_CONNECTORS_DTYPE = [("source", "uint32"), ("target", "uint32"),
                              ("weight", "float64"), ("delay", "float64")]

    @abstractmethod
    def merge(self, synapse_dynamics):
        """ Merge with the given synapse_dynamics and return the result, or\
            error if merge is not possible

        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: AbstractSynapseDynamics
        """

    @abstractmethod
    def is_same_as(self, synapse_dynamics):
        """ Determines if this synapse dynamics is the same as another

        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: bool
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

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        """ Get the SDRAM usage of the synapse dynamics parameters in bytes

        :param int n_neurons:
        :param int n_synapse_types:
        :rtype: int
        """

    @abstractmethod
    def write_parameters(self, spec, region, global_weight_scale,
                         synapse_weight_scales):
        """ Write the synapse parameters to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
            The specification to write to
        :param int region: region ID to write to
        :param float global_weight_scale: The weight scale applied globally
        :param list(float) synapse_weight_scales:
            The total weight scale applied to each synapse including the global
            weight scale
        """

    @abstractmethod
    def get_parameter_names(self):
        """ Get the parameter names available from the synapse \
            dynamics components

        :rtype: iterable(str)
        """

    @abstractmethod
    def get_max_synapses(self, n_words):
        """ Get the maximum number of synapses that can be held in the given\
            number of words

        :param int n_words: The number of words the synapses must fit in
        :rtype: int
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

    @abstractproperty
    def pad_to_length(self):
        """ The amount each row should pad to, or None if not specified
        """

    def get_delay_maximum(self, connector, synapse_info):
        """ Get the maximum delay for the synapses

        :param AbstractConnector connector:
        :param SynapseInformation synapse_info:
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
        :param SynapseInformation synapse_info:
        """
        # pylint: disable=too-many-arguments
        return connector.get_delay_variance(delays, synapse_info)

    def get_weight_mean(self, connector, synapse_info):
        """ Get the mean weight for the synapses

        :param AbstractConnector connector:
        :param SynapseInformation synapse_info:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_mean(synapse_info.weights, synapse_info)

    def get_weight_maximum(self, connector, synapse_info):
        """ Get the maximum weight for the synapses

        :param AbstractConnector connector:
        :param SynapseInformation synapse_info:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_maximum(synapse_info)

    def get_weight_minimum(self, connector, weight_random_sigma, synapse_info):
        """ Get the minimum weight for the synapses

        :param AbstractConnector connector:
        :param float weight_random_sigma:
        :param SynapseInformation synapse_info:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_minimum(
            synapse_info.weights, weight_random_sigma, synapse_info)

    def get_weight_variance(self, connector, weights, synapse_info):
        """ Get the variance in weight for the synapses

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        # pylint: disable=too-many-arguments
        return connector.get_weight_variance(weights, synapse_info)

    def convert_per_connection_data_to_rows(
            self, connection_row_indices, n_rows, data, max_n_synapses):
        """ Converts per-connection data generated from connections into\
            row-based data to be returned from get_synaptic_data

        :param ~numpy.ndarray connection_row_indices:
            The index of the row that each item should go into
        :param int n_rows:
            The number of rows
        :param ~numpy.ndarray data:
            The non-row-based data
        :param int max_n_synapses:
            The maximum number of synapses to generate in each row
        :rtype: list(~numpy.ndarray)
        """
        return [
            data[connection_row_indices == i][:max_n_synapses].reshape(-1)
            for i in range(n_rows)]

    def get_n_items(self, rows, item_size):
        """ Get the number of items in each row as 4-byte values, given the\
            item size

        :param ~numpy.ndarray rows:
        :param int item_size:
        :rtype: ~numpy.ndarray
        """
        return numpy.array([
            int(math.ceil(float(row.size) / float(item_size)))
            for row in rows], dtype="uint32").reshape((-1, 1))

    def get_words(self, rows):
        """ Convert the row data to words

        :param ~numpy.ndarray rows:
        :rtype: ~numpy.ndarray
        """
        words = [numpy.pad(
            row, (0, (4 - (row.size % 4)) & 0x3), mode="constant",
            constant_values=0).view("uint32") for row in rows]
        return words

    def get_synapse_id_by_target(self, target):
        """ Get the index of the synapse type based on the name, or None
            if the name is not found.

        :param str target: The name of the synapse
        :rtype: int or None
        """
        return None

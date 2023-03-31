# Copyright (c) 2015 The University of Manchester
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


import logging
import numpy
from pyNN.random import RandomDistribution
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)
from spinn_utilities.log import FormatAdapter
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH
from spynnaker.pyNN.exceptions import InvalidParameterType

logger = FormatAdapter(logging.getLogger(__name__))


class AbstractSynapseDynamics(object, metaclass=AbstractBase):
    """
    How do the dynamics of a synapse interact with the rest of the model.
    """

    __slots__ = ()

    @abstractmethod
    def merge(self, synapse_dynamics):
        """
        Merge with the given synapse_dynamics and return the result, or
        error if merge is not possible.

        :param AbstractSynapseDynamics synapse_dynamics:
        :rtype: AbstractSynapseDynamics
        """

    @abstractmethod
    def get_vertex_executable_suffix(self):
        """
        Get the executable suffix for a vertex for this dynamics.

        :rtype: str
        """

    @abstractproperty
    def changes_during_run(self):
        """
        Whether the synapses change during a run.

        :rtype: bool
        """

    @abstractproperty
    def weight(self):
        """
        The weight of connections.

        :rtype: float
        """

    def _round_delay(self, delay):
        """
        Round the delays to multiples of full timesteps.

        (otherwise SDRAM estimation calculations can go wrong)

        :param delay:
        :return: Rounded delay
        """
        if isinstance(delay, RandomDistribution):
            return delay
        if isinstance(delay, str):
            return delay
        new_delay = (
                numpy.rint(numpy.array(delay) *
                           SpynnakerDataView.get_simulation_time_step_per_ms())
                * SpynnakerDataView.get_simulation_time_step_ms())
        if not numpy.allclose(delay, new_delay):
            logger.warning(f"Rounding up delay in f{self} "
                           f"from {delay} to {new_delay}")
        return new_delay

    @abstractproperty
    def delay(self):
        """
        The delay of connections.

        :rtype: float
        """

    @abstractproperty
    def is_combined_core_capable(self):
        """
        Whether the synapse dynamics can run on a core combined with
        the neuron, or if a separate core is needed.

        :rtype: bool
        """

    def get_value(self, key):
        """
        Get a property.

        :param str key: the name of the property
        :rtype: Any or float or int or list(float) or list(int)
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise InvalidParameterType(
            f"Type {type(self)} does not have parameter {key}")

    def set_value(self, key, value):
        """
        Set a property.

        :param str key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        :type value: Any or float or int or list(float) or list(int)
        """
        if hasattr(self, key):
            setattr(self, key, value)
            SpynnakerDataView.set_requires_mapping()
        else:
            raise InvalidParameterType(
                f"Type {type(self)} does not have parameter {key}")

    def get_delay_maximum(self, connector, synapse_info):
        """
        Get the maximum delay for the synapses.

        :param AbstractConnector connector:
        :param ~numpy.ndarray delays:
        """
        return connector.get_delay_maximum(synapse_info)

    def get_delay_minimum(self, connector, synapse_info):
        """
        Get the minimum delay for the synapses.
        This will support the filtering of the undelayed edge
        from the graph, but requires fixes in the synaptic manager to
        happen first before this can be utilised fully.

        :param AbstractConnector connector: connector
        :param ~numpy.ndarray synapse_info: synapse info
        """
        return connector.get_delay_minimum(synapse_info)

    def get_delay_variance(self, connector, delays, synapse_info):
        """
        Get the variance in delay for the synapses.

        :param AbstractConnector connector:
        :param ~numpy.ndarray delays:
        """
        return connector.get_delay_variance(delays, synapse_info)

    def get_weight_mean(self, connector, synapse_info):
        """
        Get the mean weight for the synapses.

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        return connector.get_weight_mean(synapse_info.weights, synapse_info)

    def get_weight_maximum(self, connector, synapse_info):
        """
        Get the maximum weight for the synapses.

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        return connector.get_weight_maximum(synapse_info)

    def get_weight_variance(self, connector, weights, synapse_info):
        """
        Get the variance in weight for the synapses.

        :param AbstractConnector connector:
        :param ~numpy.ndarray weights:
        """
        return connector.get_weight_variance(weights, synapse_info)

    def get_provenance_data(self, pre_population_label, post_population_label):
        """
        Get the provenance data from this synapse dynamics object.

        :param str pre_population_label:
        :param str post_population_label:
        :rtype:
            iterable(~spinn_front_end_common.utilities.utility_objs.ProvenanceDataItem)
        """
        # pylint: disable=unused-argument
        # TODO: is this a meaningful method any more; if so, what does it do?
        return []

    def get_synapse_id_by_target(self, target):
        """
        Get the index of the synapse type based on the name, or `None`
        if the name is not found.

        :param str target: The name of the synapse
        :rtype: int or None
        """
        # pylint: disable=unused-argument
        return None

    def get_connected_vertices(self, s_info, source_vertex, target_vertex):
        """
        Get the machine vertices that are connected to each other with
        this connector.

        :param SynapseInformation s_info:
            The synapse information of the connection
        :param source_vertex: The source of the spikes
        :type source_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :param target_vertex: The target of the spikes
        :type target_vertex:
            ~pacman.model.graphs.application.ApplicationVertex
        :return: A list of tuples of (target machine vertex, list of sources)
        :rtype: list(tuple(~pacman.model.graphs.machine.MachineVertex,
            list(~pacman.model.graphs.AbstractVertex)))
        """
        # By default, just ask the connector
        return s_info.connector.get_connected_vertices(
            s_info, source_vertex, target_vertex)

    @property
    def absolute_max_atoms_per_core(self):
        """
        The absolute maximum number of atoms per core supported by this
        synapse dynamics object.

        :rtype: int
        """
        # By default, we can only support the maximum row length per core
        return POP_TABLE_MAX_ROW_LENGTH

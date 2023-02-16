# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from spinn_front_end_common.interface.provenance import (
    AbstractProvidesLocalProvenanceData)
from spynnaker.pyNN.exceptions import SynapticConfigurationException

_DynamicsStructural = None
_DynamicsSTDP = None
_DynamicsNeuromodulation = None


def are_dynamics_structural(synapse_dynamics):
    # pylint: disable=global-statement
    global _DynamicsStructural
    if _DynamicsStructural is None:
        # Avoid import loop by postponing this import
        from spynnaker.pyNN.models.neuron.synapse_dynamics import (
            AbstractSynapseDynamicsStructural)
        _DynamicsStructural = AbstractSynapseDynamicsStructural
    return isinstance(synapse_dynamics, _DynamicsStructural)


def are_dynamics_stdp(synapse_dynamics):
    # pylint: disable=global-statement
    global _DynamicsSTDP
    if _DynamicsSTDP is None:
        # Avoid import loop by postponing this import
        from spynnaker.pyNN.models.neuron.synapse_dynamics import (
            SynapseDynamicsSTDP)
        _DynamicsSTDP = SynapseDynamicsSTDP
    return isinstance(synapse_dynamics, _DynamicsSTDP)


def are_dynamics_neuromodulation(synapse_dynamics):
    # pylint: disable=global-statement
    global _DynamicsNeuromodulation
    if _DynamicsNeuromodulation is None:
        # Avoid import loop by postponing this import
        from spynnaker.pyNN.models.neuron.synapse_dynamics import (
            SynapseDynamicsNeuromodulation)
        _DynamicsNeuromodulation = SynapseDynamicsNeuromodulation
    return isinstance(synapse_dynamics, _DynamicsNeuromodulation)


class ProjectionApplicationEdge(
        ApplicationEdge, AbstractProvidesLocalProvenanceData):
    """ An edge which terminates on an :py:class:`AbstractPopulationVertex`.
    """
    __slots__ = [
        "__delay_edge",
        "__synapse_information",
        "__is_neuromodulation"
    ]

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        """
        :param AbstractPopulationVertex pre_vertex:
        :param AbstractPopulationVertex post_vertex:
        :param SynapseInformation synapse_information:
            The synapse information on this edge
        :param str label:
        """
        super().__init__(pre_vertex, post_vertex, label=label)

        # A list of all synapse information for all the projections that are
        # represented by this edge
        self.__synapse_information = [synapse_information]
        self.__is_neuromodulation = are_dynamics_neuromodulation(
            synapse_information.synapse_dynamics)

        # The edge from the delay extension of the pre_vertex to the
        # post_vertex - this might be None if no long delays are present
        self.__delay_edge = None

    def add_synapse_information(self, synapse_information):
        """
        :param SynapseInformation synapse_information:
        """
        dynamics = synapse_information.synapse_dynamics
        is_neuromodulation = are_dynamics_neuromodulation(dynamics)
        if is_neuromodulation != self.__is_neuromodulation:
            raise SynapticConfigurationException(
                "Cannot mix neuromodulated and non-neuromodulated synapses"
                f" between the same source Population {self._pre_vertex} and"
                f" target Population {self._post_vertex}")
        self.__synapse_information.append(synapse_information)

    @property
    def synapse_information(self):
        """
        :rtype: list(SynapseInformation)
        """
        return self.__synapse_information

    @property
    def delay_edge(self):
        """ Settable.

        :rtype: DelayedApplicationEdge or None
        """
        return self.__delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge):
        self.__delay_edge = delay_edge

    @property
    def is_neuromodulation(self):
        """ Check if this edge is providing neuromodulation

        :rtype: bool
        """
        return self.__is_neuromodulation

    @property
    def n_delay_stages(self):
        """
        :rtype: int
        """
        if self.__delay_edge is None:
            return 0
        return self.__delay_edge.pre_vertex.n_delay_stages

    @overrides(AbstractProvidesLocalProvenanceData.get_local_provenance_data)
    def get_local_provenance_data(self):
        for synapse_info in self.synapse_information:
            synapse_info.connector.get_provenance_data(synapse_info)

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

from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.partitioner_interfaces import AbstractSlicesConnect
from spinn_front_end_common.interface.provenance import (
    AbstractProvidesLocalProvenanceData)
from spynnaker.pyNN.exceptions import SynapticConfigurationException

_DynamicsStructural = None
_DynamicsSTDP = None
_DynamicsNeuromodulation = None


def are_dynamics_structural(synapse_dynamics):
    global _DynamicsStructural
    if _DynamicsStructural is None:
        # Avoid import loop by postponing this import
        from spynnaker.pyNN.models.neuron.synapse_dynamics import (
            AbstractSynapseDynamicsStructural)
        _DynamicsStructural = AbstractSynapseDynamicsStructural
    return isinstance(synapse_dynamics, _DynamicsStructural)


def are_dynamics_stdp(synapse_dynamics):
    global _DynamicsSTDP
    if _DynamicsSTDP is None:
        # Avoid import loop by postponing this import
        from spynnaker.pyNN.models.neuron.synapse_dynamics import (
            SynapseDynamicsSTDP)
        _DynamicsSTDP = SynapseDynamicsSTDP
    return isinstance(synapse_dynamics, _DynamicsSTDP)


def are_dynamics_neuromodulation(synapse_dynamics):
    global _DynamicsNeuromodulation
    if _DynamicsNeuromodulation is None:
        # Avoid import loop by postponing this import
        from spynnaker.pyNN.models.neuron.synapse_dynamics import (
            SynapseDynamicsNeuromodulation)
        _DynamicsNeuromodulation = SynapseDynamicsNeuromodulation
    return isinstance(synapse_dynamics, _DynamicsNeuromodulation)


class ProjectionApplicationEdge(
        ApplicationEdge, AbstractSlicesConnect,
        AbstractProvidesLocalProvenanceData):
    """ An edge which terminates on an :py:class:`AbstractPopulationVertex`.
    """
    __slots__ = [
        "__delay_edge",
        "__synapse_information",
        "__filter",
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

        # By default, allow filtering
        self.__filter = True

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

    def set_filter(self, do_filter):
        """ Set the ability to filter or not

        @param bool do_filter: Whether to allow filtering
        """
        self.__filter = do_filter

    @property
    def n_delay_stages(self):
        """
        :rtype: int
        """
        if self.__delay_edge is None:
            return 0
        return self.__delay_edge.pre_vertex.n_delay_stages

    def get_machine_edge(self, pre_vertex, post_vertex):
        """ Get a specific machine edge of this edge

        :param PopulationMachineVertex pre_vertex:
            The vertex at the start of the machine edge
        :param PopulationMachineVertex post_vertex:
            The vertex at the end of the machine edge
        :rtype: ~pacman.model.graphs.machine.MachineEdge or None
        """
        return self.__machine_edges_by_slices.get(
            (pre_vertex.vertex_slice, post_vertex.vertex_slice), None)

    @overrides(AbstractSlicesConnect.could_connect)
    def could_connect(self, src_machine_vertex, dest_machine_vertex):
        if not self.__filter:
            return False
        for synapse_info in self.__synapse_information:
            # Structual Plasticity can learn connection not originally included
            if are_dynamics_structural(synapse_info.synapse_dynamics):
                return True
            if synapse_info.connector.could_connect(
                    synapse_info, src_machine_vertex, dest_machine_vertex):
                return True
        return False

    @overrides(AbstractProvidesLocalProvenanceData.get_local_provenance_data)
    def get_local_provenance_data(self):
        for synapse_info in self.synapse_information:
            synapse_info.connector.get_provenance_data(synapse_info)

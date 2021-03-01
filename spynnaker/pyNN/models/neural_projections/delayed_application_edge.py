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
from spynnaker.pyNN.models.neural_projections\
    .projection_application_edge import are_dynamics_structural


class DelayedApplicationEdge(ApplicationEdge, AbstractSlicesConnect):

    __slots__ = [
        "__synapse_information",
        "__machine_edges_by_slices",
        "__undelayed_edge"]

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, undelayed_edge,
            label=None):
        """
        :param DelayExtensionVertex pre_vertex:
            The delay extension at the start of the edge
        :param AbstractPopulationVertex post_vertex:
            The target of the synapses
        :param synapse_information:
            The synapse information on this edge
        :type synapse_information:
            SynapseInformation or iterable(SynapseInformation)
        :param ProjectionApplicationEdge undelayed_edge:
            The edge that is used for projections without extended delays
        :param str label:
            The edge label
        """
        super().__init__(pre_vertex, post_vertex, label=label)
        if hasattr(synapse_information, '__iter__'):
            self.__synapse_information = synapse_information
        else:
            self.__synapse_information = [synapse_information]
        self.__undelayed_edge = undelayed_edge

        # Keep the machine edges by pre- and post-slice
        self.__machine_edges_by_slices = dict()

    @property
    def synapse_information(self):
        """
        :rtype: list(SynapseInformation)
        """
        return self.__synapse_information

    def add_synapse_information(self, synapse_information):
        """
        :param SynapseInformation synapse_information:
        """
        self.__synapse_information.append(synapse_information)

    @property
    def undelayed_edge(self):
        """ Get the edge that for projections without extended delays

        :rtype: ProjectionApplicationEdge
        """
        return self.__undelayed_edge

    @overrides(ApplicationEdge.remember_associated_machine_edge)
    def remember_associated_machine_edge(self, machine_edge):
        super().remember_associated_machine_edge(machine_edge)
        self.__machine_edges_by_slices[
            machine_edge.pre_vertex.vertex_slice,
            machine_edge.post_vertex.vertex_slice] = machine_edge

    def get_machine_edge(self, pre_vertex, post_vertex):
        """ Get a specific machine edge from this edge

        :param DelayExtensionMachineVertex pre_vertex:
            The vertex at the start of the machine edge
        :param PopulationMachineVertex post_vertex:
            The vertex at the end of the machine edge
        :rtype: ~pacman.model.graphs.machine.MachineEdge or None
        """
        return self.__machine_edges_by_slices.get(
            (pre_vertex.vertex_slice, post_vertex.vertex_slice), None)

    @overrides(AbstractSlicesConnect.could_connect)
    def could_connect(self, pre_slice, post_slice):
        for synapse_info in self.__synapse_information:
            # Structual Plasticity can learn connection not originally included
            if are_dynamics_structural(synapse_info.synapse_dynamics):
                return True
            if synapse_info.connector.could_connect(
                    synapse_info, pre_slice, post_slice):
                return True
        return False

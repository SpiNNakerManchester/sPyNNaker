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

from pacman.model.graphs.machine import MachineEdge


class DelayedMachineEdge(MachineEdge):
    __slots__ = [
        "__synapse_information",
        "__undelayed_edge"]

    def __init__(
            self, synapse_information, pre_vertex, post_vertex, app_edge,
            label=None, weight=1):
        """
        :param list(SynapseInformation) synapse_information:
        :param DelayExtensionMachineVertex pre_vertex:
        :param PopulationMachineVertex post_vertex:
        :param str label:
        :param int weight:
        """
        # pylint: disable=too-many-arguments
        super(DelayedMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label, traffic_weight=weight,
            app_edge=app_edge)
        self.__synapse_information = synapse_information
        self.__undelayed_edge = None

    @property
    def undelayed_edge(self):
        """ Get the edge used for Projections without extended delays

        :rtype: ProjectionMachineEdge or None
        """
        return self.__undelayed_edge

    @undelayed_edge.setter
    def undelayed_edge(self, undelayed_edge):
        """ Set the edge used for Projections without extended delays

        :param ProjectionMachineEdge undelayed_edge:
            The edge to set
        """
        self.__undelayed_edge = undelayed_edge

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
from .delayed_machine_edge import DelayedMachineEdge


class DelayedApplicationEdge(ApplicationEdge):
    __slots__ = [
        "__synapse_information"]

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        """
        :param DelayExtensionVertex pre_vertex:
        :param AbstractPopulationVertex post_vertex:
        :param SynapseInformation synapse_information:
        :param str label:
        """
        super(DelayedApplicationEdge, self).__init__(
            pre_vertex, post_vertex, label=label)
        self.__synapse_information = [synapse_information]

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

    @overrides(ApplicationEdge._create_machine_edge)
    def _create_machine_edge(self, pre_vertex, post_vertex, label):
        return DelayedMachineEdge(
            self.__synapse_information, pre_vertex, post_vertex, self, label)

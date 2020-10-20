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

from pyNN.random import RandomDistribution
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities import utility_calls
from pacman.model.graphs.machine import MachineEdge
from spinn_front_end_common.interface.provenance import (
    AbstractProvidesLocalProvenanceData)
from spynnaker.pyNN.models.abstract_models import AbstractWeightUpdatable


class ProjectionMachineEdge(
        MachineEdge, AbstractWeightUpdatable,
        AbstractProvidesLocalProvenanceData):
    __slots__ = [
        "__synapse_information",
        "__delay_edge"]

    def __init__(
            self, synapse_information, pre_vertex, post_vertex, app_edge,
            label=None, traffic_weight=1):
        """
        :param list(SynapseInformation) synapse_information:
        :param PopulationMachineVertex pre_vertex:
        :param PopulationMachineVertex post_vertex:
        :param str label:
        :param int traffic_weight:
        """
        # pylint: disable=too-many-arguments
        super(ProjectionMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label, app_edge=app_edge,
            traffic_weight=traffic_weight)

        self.__synapse_information = synapse_information
        self.__delay_edge = None

    @property
    def delay_edge(self):
        """ Get the matching delay edge of this edge

        :rtype: DelayedMachineEdge or None
        """
        return self.__delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge):
        """ Set the matching delay edge of this edge

        :param DelayMachineEdge delay_edge: The edge to set
        """
        self.__delay_edge = delay_edge

    @property
    def synapse_information(self):
        """
        :rtype: list(SynapseInformation)
        """
        return self.__synapse_information

    @overrides(AbstractWeightUpdatable.update_weight)
    def update_weight(self):
        pre_vertex = self.pre_vertex.app_vertex
        pre_vertex_slice = self.pre_vertex.vertex_slice

        weight = 0
        for synapse_info in self.__synapse_information:
            new_weight = synapse_info.connector.\
                get_n_connections_to_post_vertex_maximum(synapse_info)
            new_weight *= pre_vertex_slice.n_atoms
            if hasattr(pre_vertex, "rate"):
                rate = pre_vertex.rate
                if hasattr(rate, "__getitem__"):
                    rate = max(rate)
                elif isinstance(rate, RandomDistribution):
                    rate = utility_calls.get_maximum_probable_value(
                        rate, pre_vertex_slice.n_atoms)
                new_weight *= rate
            elif hasattr(pre_vertex, "spikes_per_second"):
                new_weight *= pre_vertex.spikes_per_second
            weight += new_weight

        self._traffic_weight = weight

    @overrides(AbstractProvidesLocalProvenanceData.get_local_provenance_data)
    def get_local_provenance_data(self):
        prov_items = list()
        for synapse_info in self.__synapse_information:
            prov_items.extend(
                synapse_info.connector.get_provenance_data(synapse_info))
            prov_items.extend(
                synapse_info.synapse_dynamics.get_provenance_data(
                    self.pre_vertex.label, self.post_vertex.label))
        return prov_items

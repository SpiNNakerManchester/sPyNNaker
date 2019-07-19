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
from pacman.model.graphs.machine import MachineEdge
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector)
from spynnaker.pyNN.models.abstract_models import AbstractFilterableEdge


class DelayedMachineEdge(MachineEdge, AbstractFilterableEdge):
    __slots__ = [
        "__synapse_information"]

    def __init__(
            self, synapse_information, pre_vertex, post_vertex,
            label=None, weight=1):
        # pylint: disable=too-many-arguments
        super(DelayedMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label, traffic_weight=weight)
        self.__synapse_information = synapse_information

    @overrides(AbstractFilterableEdge.filter_edge)
    def filter_edge(self, graph_mapper):

        # Filter one-to-one connections that are out of range
        for synapse_info in self.__synapse_information:
            if isinstance(synapse_info.connector, OneToOneConnector):
                pre_lo = graph_mapper.get_slice(self.pre_vertex).lo_atom
                pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom
                post_lo = graph_mapper.get_slice(self.post_vertex).lo_atom
                post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom
                if pre_hi < post_lo or pre_lo > post_hi:
                    return True
        return False

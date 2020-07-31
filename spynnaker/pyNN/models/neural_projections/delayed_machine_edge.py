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
    OneToOneConnector, FromListConnector)
from spynnaker.pyNN.models.abstract_models import AbstractFilterableEdge


class DelayedMachineEdge(MachineEdge, AbstractFilterableEdge):
    __slots__ = [
        "__synapse_information"]

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

    @overrides(AbstractFilterableEdge.filter_edge)
    def filter_edge(self):
        # Filter one-to-one connections that are out of range
        n_filtered = 0
        for synapse_info in self.__synapse_information:
            if isinstance(synapse_info.connector, OneToOneConnector):
                pre = self.pre_vertex.vertex_slice
                post = self.post_vertex.vertex_slice
                # Filter edge if both are views and outside limits
                if (synapse_info.prepop_is_view and
                        synapse_info.postpop_is_view):
                    pre_lo = synapse_info.pre_population._indexes[0]
                    pre_hi = synapse_info.pre_population._indexes[-1]
                    post_lo = synapse_info.post_population._indexes[0]
                    post_hi = synapse_info.post_population._indexes[-1]
                    if ((pre.hi_atom - pre_lo < post.lo_atom - post_lo) or
                            (pre.lo_atom - pre_lo > post.hi_atom - post_lo) or
                            (pre.hi_atom < pre_lo) or
                            (pre.lo_atom > pre_hi) or
                            (post.hi_atom < post_lo) or
                            (post.lo_atom > post_hi)):
                        n_filtered += 1
                # Filter edge if pre-pop is outside limit and post_lo is bigger
                # than n_pre_neurons
                elif synapse_info.prepop_is_view:
                    pre_lo = synapse_info.pre_population._indexes[0]
                    pre_hi = synapse_info.pre_population._indexes[-1]
                    if ((pre.hi_atom - pre_lo < post.lo_atom) or
                            (pre.lo_atom - pre_lo > post.hi_atom) or
                            (pre.hi_atom < pre_lo) or
                            (pre.lo_atom > pre_hi)):
                        n_filtered += 1
                # Filter edge if post-pop is outside limit and pre_lo is bigger
                # than n_post_neurons
                elif synapse_info.postpop_is_view:
                    post_lo = synapse_info.post_population._indexes[0]
                    post_hi = synapse_info.post_population._indexes[-1]
                    if ((pre.hi_atom < post.lo_atom - post_lo) or
                            (pre.lo_atom > post.hi_atom - post_lo) or
                            (post.hi_atom < post_lo) or
                            (post.lo_atom > post_hi)):
                        n_filtered += 1
                # Filter edge in the usual scenario with normal populations
                elif pre.hi_atom < post.lo_atom or pre.lo_atom > post.hi_atom:
                    n_filtered += 1
            elif isinstance(synapse_info.connector, FromListConnector):
                pre_hi = self.pre_vertex.vertex_slice.hi_atom
                post_hi = self.post_vertex.vertex_slice.hi_atom
                pre_slices = self.pre_vertex.app_vertex.vertex_slices
                post_slices = self.post_vertex.app_vertex.vertex_slices
                # run through connection list and check for any connections
                # between the pre and post vertices that could be filtered
                n_connections = synapse_info.connector.get_n_connections(
                    pre_slices, post_slices, pre_hi, post_hi)
                if n_connections == 0:
                    n_filtered += 1

        return n_filtered == len(self.__synapse_information)

    @staticmethod
    def __no_overlap(pre_vertex, post_vertex):
        pre = pre_vertex.vertex_slice
        post = post_vertex.vertex_slice
        return pre.hi_atom < post.lo_atom or pre.lo_atom > post.hi_atom

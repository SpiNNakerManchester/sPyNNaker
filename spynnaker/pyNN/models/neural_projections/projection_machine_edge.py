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
from spynnaker.pyNN.models.neural_projections.connectors import (
    OneToOneConnector, FromListConnector)
from spynnaker.pyNN.models.abstract_models import (
    AbstractWeightUpdatable, AbstractFilterableEdge)


class ProjectionMachineEdge(
        MachineEdge, AbstractFilterableEdge,
        AbstractWeightUpdatable, AbstractProvidesLocalProvenanceData):
    __slots__ = [
        "__synapse_information"]

    def __init__(
            self, synapse_information, pre_vertex, post_vertex,
            label=None, traffic_weight=1):
        # pylint: disable=too-many-arguments
        super(ProjectionMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label,
            traffic_weight=traffic_weight)

        self.__synapse_information = synapse_information

    @property
    def synapse_information(self):
        return self.__synapse_information

    @overrides(AbstractFilterableEdge.filter_edge)
    def filter_edge(self, graph_mapper):
        # Filter one-to-one connections that are out of range
        # Note: there may be other connectors stored on the same edge!
        n_filtered = 0
        for synapse_info in self.__synapse_information:
            if isinstance(synapse_info.connector, OneToOneConnector):
                pre_lo = graph_mapper.get_slice(self.pre_vertex).lo_atom
                pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom
                post_lo = graph_mapper.get_slice(self.post_vertex).lo_atom
                post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom
                # Filter edge if both are views and outside limits
                if ((synapse_info.prepop_is_view) and
                        (synapse_info.postpop_is_view)):
                    prepop_lo = synapse_info.pre_population._indexes[0]
                    prepop_hi = synapse_info.pre_population._indexes[-1]
                    postpop_lo = synapse_info.post_population._indexes[0]
                    postpop_hi = synapse_info.post_population._indexes[-1]
                    # Get test values
                    pre_lo_test = pre_lo - prepop_lo
                    pre_hi_test = pre_hi - prepop_lo
                    post_lo_test = post_lo - postpop_lo
                    post_hi_test = post_hi - postpop_lo
                    if ((pre_hi_test < post_lo_test) or
                            (pre_lo_test > post_hi_test) or
                            (pre_hi < prepop_lo) or (pre_lo > prepop_hi) or
                            (post_hi < postpop_lo) or (post_lo > postpop_hi)):
                        n_filtered += 1
                # Filter edge if pre-pop is outside limit and post_lo is bigger
                # than n_pre_neurons
                elif synapse_info.prepop_is_view:
                    prepop_lo = synapse_info.pre_population._indexes[0]
                    prepop_hi = synapse_info.pre_population._indexes[-1]
                    # Get test values
                    pre_lo_test = pre_lo - prepop_lo
                    pre_hi_test = pre_hi - prepop_lo
                    if ((pre_hi_test < post_lo) or
                            (pre_lo_test > post_hi) or
                            (pre_hi < prepop_lo) or (pre_lo > prepop_hi)):
                        n_filtered += 1
                # Filter edge if post-pop is outside limit and pre_lo is bigger
                # than n_post_neurons
                elif synapse_info.postpop_is_view:
                    postpop_lo = synapse_info.post_population._indexes[0]
                    postpop_hi = synapse_info.post_population._indexes[-1]
                    # Get test values
                    post_lo_test = post_lo - postpop_lo
                    post_hi_test = post_hi - postpop_lo
                    if ((pre_hi < post_lo_test) or
                            (pre_lo > post_hi_test) or
                            (post_hi < postpop_lo) or (post_lo > postpop_hi)):
                        n_filtered += 1
                # Filter edge in the usual scenario with normal populations
                else:
                    if pre_hi < post_lo or pre_lo > post_hi:
                        n_filtered += 1
            elif isinstance(synapse_info.connector, FromListConnector):
                pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom
                post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom
                pre_app_vertex = graph_mapper.get_application_vertex(
                    self.pre_vertex)
                post_app_vertex = graph_mapper.get_application_vertex(
                    self.post_vertex)
                pre_slices = graph_mapper.get_slices(pre_app_vertex)
                post_slices = graph_mapper.get_slices(post_app_vertex)
                # run through connection list and check for any connections
                # between the pre and post vertices that could be filtered
                n_connections = synapse_info.connector.get_n_connections(
                    pre_slices, post_slices, pre_hi, post_hi)
                if n_connections == 0:
                    n_filtered += 1

        return n_filtered == len(self.__synapse_information)

    @overrides(AbstractWeightUpdatable.update_weight)
    def update_weight(self, graph_mapper):
        pre_vertex = graph_mapper.get_application_vertex(
            self.pre_vertex)
        pre_vertex_slice = graph_mapper.get_slice(
            self.pre_vertex)

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

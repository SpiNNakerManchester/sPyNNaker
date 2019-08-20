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

import logging
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineEdge
from spynnaker.pyNN.models.abstract_models import (
    AbstractWeightUpdatable, AbstractFilterableEdge)

logger = logging.getLogger(__name__)


class DelayAfferentMachineEdge(
        MachineEdge, AbstractFilterableEdge, AbstractWeightUpdatable):
    __slots__ = []

    def __init__(self, pre_vertex, post_vertex, label, app_edge, weight=1):
        super(DelayAfferentMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label, app_edge=app_edge,
            traffic_weight=weight)

    @overrides(AbstractFilterableEdge.filter_edge)
    def filter_edge(self, graph_mapper):
        pre_lo = self.pre_vertex.vertex_slice.lo_atom
        pre_hi = self.pre_vertex.vertex_slice.hi_atom
        post_lo = self.post_vertex.vertex_slice.lo_atom
        post_hi = self.post_vertex.vertex_slice.hi_atom
        return (pre_lo != post_lo) or (pre_hi != post_hi)

    @overrides(AbstractWeightUpdatable.update_weight)
    def update_weight(self):
        self._traffic_weight = self.pre_vertex.vertex_slice.n_atoms

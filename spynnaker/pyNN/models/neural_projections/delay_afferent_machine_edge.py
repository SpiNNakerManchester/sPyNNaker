import logging
from spinn_utilities.overrides import overrides
from pacman.model.graphs.machine import MachineEdge
from spynnaker.pyNN.models.abstract_models import (
    AbstractWeightUpdatable, AbstractFilterableEdge)

logger = logging.getLogger(__name__)


class DelayAfferentMachineEdge(
        MachineEdge, AbstractFilterableEdge, AbstractWeightUpdatable):
    __slots__ = []

    def __init__(self, pre_vertex, post_vertex, label, weight=1):
        super(DelayAfferentMachineEdge, self).__init__(
            pre_vertex, post_vertex, label=label, traffic_weight=weight)

    @overrides(AbstractFilterableEdge.filter_edge)
    def filter_edge(self, graph_mapper):
        pre_lo = graph_mapper.get_slice(self.pre_vertex).lo_atom
        pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom
        post_lo = graph_mapper.get_slice(self.post_vertex).lo_atom
        post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom
        return (pre_lo != post_lo) or (pre_hi != post_hi)

    @overrides(AbstractWeightUpdatable.update_weight)
    def update_weight(self, graph_mapper):
        pre_vertex_slice = graph_mapper.get_slice(self.pre_vertex)
        self._traffic_weight = pre_vertex_slice.n_atoms

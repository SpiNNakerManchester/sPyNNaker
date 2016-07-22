from spynnaker.pyNN.models.abstract_models.abstract_weight_updatable \
    import AbstractWeightUpdatable
from pacman.model.graph.machine.simple_machine_edge \
    import SimpleMachineEdge
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge import\
    AbstractFilterableEdge

import logging
logger = logging.getLogger(__name__)


class DelayAfferentMachineEdge(
        SimpleMachineEdge, AbstractFilterableEdge,
        AbstractWeightUpdatable):

    def __init__(self, pre_vertex, post_vertex):
        SimpleMachineEdge.__init__(
            self, pre_vertex, post_vertex)
        AbstractFilterableEdge.__init__(self)
        AbstractWeightUpdatable.__init__(self)

    def filter_edge(self, graph_mapper):
        pre_lo = graph_mapper.get_slice(self.pre_vertex).lo_atom
        pre_hi = graph_mapper.get_slice(self.pre_vertex).hi_atom
        post_lo = graph_mapper.get_slice(self.post_vertex).lo_atom
        post_hi = graph_mapper.get_slice(self.post_vertex).hi_atom
        if (pre_lo != post_lo) or (pre_hi != post_hi):
            return True
        return False

    def update_weight(self, graph_mapper):
        pre_vertex_slice = graph_mapper.get_slice(self.pre_vertex)
        self._weight = pre_vertex_slice.n_atoms

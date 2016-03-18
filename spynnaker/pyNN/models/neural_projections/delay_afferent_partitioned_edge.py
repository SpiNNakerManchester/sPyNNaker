from spynnaker.pyNN.models.abstract_models.abstract_weight_updatable \
    import AbstractWeightUpdatable
from pacman.model.partitioned_graph.multi_cast_partitioned_edge \
    import MultiCastPartitionedEdge
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge import\
    AbstractFilterableEdge

import logging
logger = logging.getLogger(__name__)


class DelayAfferentPartitionedEdge(
        MultiCastPartitionedEdge, AbstractFilterableEdge,
        AbstractWeightUpdatable):

    def __init__(self, presubvertex, postsubvertex):
        MultiCastPartitionedEdge.__init__(
            self, presubvertex, postsubvertex)
        AbstractFilterableEdge.__init__(self)
        AbstractWeightUpdatable.__init__(self)

    def filter_sub_edge(self, graph_mapper):
        """ Filter a subedge of this edge if the edge is not a one-to-one edge
        """
        pre_sub_lo = \
            graph_mapper.get_subvertex_slice(self._pre_subvertex).lo_atom
        pre_sub_hi = \
            graph_mapper.get_subvertex_slice(self._pre_subvertex).hi_atom
        post_sub_lo = \
            graph_mapper.get_subvertex_slice(self._post_subvertex).lo_atom
        post_sub_hi = \
            graph_mapper.get_subvertex_slice(self._post_subvertex).hi_atom
        if (pre_sub_lo != post_sub_lo) or (pre_sub_hi != post_sub_hi):
            return True
        return False

    def update_weight(self, graph_mapper):
        pre_vertex_slice = graph_mapper.get_subvertex_slice(
            self._pre_subvertex)
        return pre_vertex_slice.n_atoms

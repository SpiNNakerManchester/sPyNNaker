from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge import\
    AbstractFilterableEdge


class DelayAfferentPartitionableEdge(PartitionableEdge, AbstractFilterableEdge):
    
    def __init__(self, prevertex, delayvertex, label=None):
        PartitionableEdge.__init__(self, prevertex, delayvertex, label=label)
        AbstractFilterableEdge.__init__(self)

    def filter_sub_edge(self, subedge, graph_mapper):
        """
        Filters a subedge of this edge if the edge is not a one-to-one edge
        """
        pre_sub_lo = \
            graph_mapper.get_subvertex_slice(subedge.pre_subvertex).lo_atom
        pre_sub_hi = \
            graph_mapper.get_subvertex_slice(subedge.pre_subvertex).hi_atom
        post_sub_lo = \
            graph_mapper.get_subvertex_slice(subedge.post_subvertex).lo_atom
        post_sub_hi = \
            graph_mapper.get_subvertex_slice(subedge.post_subvertex).hi_atom
        if (pre_sub_lo != post_sub_lo) or (pre_sub_hi != post_sub_hi):
            return True
        return False

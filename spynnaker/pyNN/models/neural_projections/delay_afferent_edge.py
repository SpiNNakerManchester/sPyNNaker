from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge


class DelayAfferentPartitionableEdge(PartitionableEdge):
    
    def __init__(self, prevertex, delayvertex, label=None):
        PartitionableEdge.__init__(self, prevertex, delayvertex, label=label)

    @staticmethod
    def filter_sub_edge(subedge, graph_mapper):
        """
        Filters a subedge of this edge if the edge is not a one-to-one edge
        """
        pre_sub_lo = \
            graph_mapper.get_subvertex_slice(subedge.presubvertex).lo_atom
        pre_sub_hi = \
            graph_mapper.get_subvertex_slice(subedge.presubvertex).hi_atom
        post_sub_lo = \
            graph_mapper.get_subvertex_slice(subedge.postsubvertex).lo_atom
        post_sub_hi = \
            graph_mapper.get_subvertex_slice(subedge.postsubvertex).hi_atom
        if (pre_sub_lo != post_sub_lo) or (pre_sub_hi != post_sub_hi):
            return True
        return False

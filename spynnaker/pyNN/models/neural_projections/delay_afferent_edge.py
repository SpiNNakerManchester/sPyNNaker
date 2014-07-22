from pacman.model.graph.edge import Edge


class DelayAfferentEdge(Edge):
    
    def __init__(self, prevertex, delayvertex, label=None):
        Edge.__init__(self, prevertex, delayvertex, label=label)

    @staticmethod
    def filter_sub_edge(subedge):
        """
        Filters a subedge of this edge if the edge is not a one-to-one edge
        """
        if ((subedge.presubvertex.lo_atom != subedge.postsubvertex.lo_atom) or
           (subedge.presubvertex.hi_atom != subedge.postsubvertex.hi_atom)):
            return True
        return False

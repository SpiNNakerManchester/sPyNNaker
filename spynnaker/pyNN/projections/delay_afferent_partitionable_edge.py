from pacman.model.partitionable_graph.multi_cast_partitionable_edge \
    import MultiCastPartitionableEdge
from spynnaker.pyNN.projections.delay_afferent_partitioned_edge \
    import DelayAfferentPartitionedEdge


class DelayAfferentPartitionableEdge(MultiCastPartitionableEdge):

    def __init__(self, prevertex, delayvertex, label=None):
        MultiCastPartitionableEdge.__init__(self, prevertex, delayvertex,
                                            label=label)

    def create_subedge(self, pre_subvertex, pre_subvertex_slice,
                       post_subvertex, post_subvertex_slice, constraints=None,
                       label=None):
        """
        """
        if constraints is None:
            constraints = list()
        constraints.extend(self.constraints)
        return DelayAfferentPartitionedEdge(
            self, pre_subvertex, pre_subvertex_slice, post_subvertex,
            post_subvertex_slice, constraints)

    def is_multi_cast_partitionable_edge(self):
        """
        """
        return True

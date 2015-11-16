from pacman.model.partitionable_graph.multi_cast_partitionable_edge import \
    MultiCastPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_partitioned_edge \
    import DelayAfferentPartitionedEdge


class DelayAfferentPartitionableEdge(MultiCastPartitionableEdge):

    def __init__(self, prevertex, delayvertex, label=None):
        MultiCastPartitionableEdge.__init__(self, prevertex, delayvertex,
                                            label=label)

    def create_subedge(self, pre_subvertex, post_subvertex, constraints=None,
                       label=None):
        """ Create a subedge between the pre_subvertex and the post_subvertex

        :param pre_subvertex: The subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param post_subvertex: The subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param label: The label to give the edge.  If not specified, and the\
                    edge has no label, the subedge will have no label.  If not\
                    specified and the edge has a label, a label will be\
                    provided
        :type label: str
        :return: The created subedge
        :rtype: :py:class:`pacman.model.subgraph.subedge.PartitionedEdge`
        :raise None: does not raise any known exceptions
        """
        if constraints is None:
            constraints = list()
        constraints.extend(self.constraints)
        return DelayAfferentPartitionedEdge(pre_subvertex, post_subvertex,
                                            constraints)

    def is_multi_cast_partitionable_edge(self):
        """helper method for isinstance

        :return:
        """
        return True

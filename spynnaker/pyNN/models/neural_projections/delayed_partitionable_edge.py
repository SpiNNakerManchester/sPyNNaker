from spynnaker.pyNN.models.neural_projections.delayed_partitioned_edge \
    import DelayedPartitionedEdge
from pacman.model.partitionable_graph.multi_cast_partitionable_edge \
    import MultiCastPartitionableEdge


class DelayedPartitionableEdge(MultiCastPartitionableEdge):

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        MultiCastPartitionableEdge.__init__(
            self, pre_vertex, post_vertex, label=label)
        self._synapse_information = [synapse_information]

    def add_synapse_information(self, synapse_information):
        self._synapse_information.append(synapse_information)

    def create_subedge(self, pre_subvertex, post_subvertex, label=None):
        return DelayedPartitionedEdge(
            self._synapse_information, pre_subvertex, post_subvertex, label)

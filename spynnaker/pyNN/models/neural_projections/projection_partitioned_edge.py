from pacman.model.partitioned_graph.partitioned_edge import PartitionedEdge
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge import \
    AbstractFilterableEdge


class ProjectionPartitionedEdge(PartitionedEdge, AbstractFilterableEdge):
    
    def __init__(self, presubvertex, postsubvertex, associated_edge):
        PartitionedEdge.__init__(self, presubvertex, postsubvertex)
        AbstractFilterableEdge.__init__(self)
        self._synapse_sublist = None
        self._associated_edge = associated_edge

    def get_synapse_sublist(self, graph_mapper):
        """
        Gets the synapse list for this subedge
        """
        pre_vertex_slice = \
            graph_mapper.get_subvertex_slice(self._pre_subvertex)
        post_vertex_slice = \
            graph_mapper.get_subvertex_slice(self._post_subvertex)
        if self._synapse_sublist is None:
            self._synapse_sublist = \
                self._associated_edge.synapse_list.create_atom_sublist(
                    pre_vertex_slice, post_vertex_slice)
        return self._synapse_sublist
    
    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self._synapse_sublist = None

    def filter_sub_edge(self, subedge, graph_mapper):
        """determines if theres an actual connection in this subedge in temrs of
        synaptic data

        """
        if self._synapse_sublist is None:
            self.get_synapse_sublist(graph_mapper)

        pre_vertex_slice = graph_mapper.get_subvertex_slice(self._pre_subvertex)
        post_vertex_slice = \
            graph_mapper.get_subvertex_slice(self._post_subvertex)

        return self._synapse_sublist.is_connected(pre_vertex_slice,
                                                  post_vertex_slice)
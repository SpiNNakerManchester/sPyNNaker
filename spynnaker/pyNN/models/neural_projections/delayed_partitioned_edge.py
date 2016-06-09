from pacman.model.partitioned_graph.multi_cast_partitioned_edge \
    import MultiCastPartitionedEdge
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge \
    import AbstractFilterableEdge


class DelayedPartitionedEdge(MultiCastPartitionedEdge, AbstractFilterableEdge):

    def __init__(
            self, synapse_information, pre_subvertex, post_subvertex,
            label=None):
        MultiCastPartitionedEdge.__init__(
            self, pre_subvertex, post_subvertex, label=label)
        AbstractFilterableEdge.__init__(self)
        self._synapse_information = synapse_information

    def filter_sub_edge(self, graph_mapper):
        pre_vertex = graph_mapper.get_vertex_from_subvertex(
            self._pre_subvertex)
        pre_slice_index = graph_mapper.get_subvertex_index(self._pre_subvertex)
        pre_vertex_slice = graph_mapper.get_subvertex_slice(
            self._pre_subvertex)
        pre_slices = graph_mapper.get_subvertex_slices(pre_vertex)
        post_vertex = graph_mapper.get_vertex_from_subvertex(
            self._post_subvertex)
        post_slice_index = graph_mapper.get_subvertex_index(
            self._post_subvertex)
        post_vertex_slice = graph_mapper.get_subvertex_slice(
            self._post_subvertex)
        post_slices = graph_mapper.get_subvertex_slices(post_vertex)

        n_connections = 0
        for synapse_info in self._synapse_information:
            n_connections += synapse_info.connector.\
                get_n_connections_to_post_vertex_maximum(
                    pre_slices, pre_slice_index, post_slices,
                    post_slice_index, pre_vertex_slice, post_vertex_slice)
            if n_connections > 0:
                return False

        return n_connections == 0

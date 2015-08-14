from pacman.model.partitioned_graph.multi_cast_partitioned_edge \
    import MultiCastPartitionedEdge
from spynnaker.pyNN.models.common.abstract_filterable_edge \
    import AbstractFilterableEdge


class ProjectionPartitionedEdge(MultiCastPartitionedEdge,
                                AbstractFilterableEdge):

    def __init__(self, edge, presubvertex, presubvertex_slice, postsubvertex,
                 postsubvertex_slice, constraints):
        MultiCastPartitionedEdge.__init__(
            self, presubvertex, postsubvertex, constraints)
        AbstractFilterableEdge.__init__(self)
        self._edge = edge
        self._presubvertex_slice = presubvertex_slice
        self._postsubvertex_slice = postsubvertex_slice
        self._synapse_sublist = None
        self._weight_scales = None

    @property
    def edge(self):
        return self._edge

    @property
    def presubvertex_slice(self):
        return self._presubvertex_slice

    @property
    def postsubvertex_slice(self):
        return self._postsubvertex_slice

    @property
    def weight_scales(self):
        return self._weight_scales

    # **YUCK** setters don't work properly with inheritance
    def weight_scales_setter(self, value):
        self._weight_scales = value

    def get_synapse_sublist(self):
        """
        Gets the synapse list for this subedge
        """
        if self._synapse_sublist is None:
            self._synapse_sublist = \
                self._edge.synapse_list.create_atom_sublist(
                    self._presubvertex_slice, self._postsubvertex_slice)
        return self._synapse_sublist

    def get_n_rows(self, graph_mapper):
        pre_vertex_slice = graph_mapper.get_subvertex_slice(
            self._pre_subvertex)
        return pre_vertex_slice.n_atoms

    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self._synapse_sublist = None

    def filter_sub_edge(self):
        """
        """
        return not self._edge.synapse_list.is_connected(
            self._presubvertex_slice, self._postsubvertex_slice)

    @property
    def synapse_sublist(self):
        return self._synapse_sublist

    def is_multi_cast_partitioned_edge(self):
        return True

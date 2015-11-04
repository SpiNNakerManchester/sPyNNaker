"""
EdgeToNKeysMapper
"""

# pacman imports
from pacman.model.routing_info.dict_based_partitioned_edge_n_keys_map import \
    DictBasedPartitionedEdgeNKeysMap
from pacman.utilities.utility_objs.progress_bar import ProgressBar

# front end common imports
from spinn_front_end_common.abstract_models.\
    abstract_provides_incoming_edge_constraints import \
    AbstractProvidesIncomingEdgeConstraints
from spinn_front_end_common.abstract_models.\
    abstract_provides_n_keys_for_edge import \
    AbstractProvidesNKeysForEdge
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints import \
    AbstractProvidesOutgoingEdgeConstraints


class EdgeToNKeysMapper(object):
    """
    generates a mapping between each edge and the number of keys it requires.
    """

    def __call__(self, partitioned_graph, graph_mapper):
        """
        Generate an n_keys map for the graph and add constraints
        :param partitioned_graph:
        :param graph_mapper:
        :return:
        """
        progress_bar = ProgressBar(
            len(partitioned_graph.subedges),
            "Deducing edge to number of keys map")

        n_keys_map = DictBasedPartitionedEdgeNKeysMap()
        for edge in partitioned_graph.subedges:
            vertex_slice = graph_mapper.get_subvertex_slice(
                edge.pre_subvertex)
            super_edge = (graph_mapper
                          .get_partitionable_edge_from_partitioned_edge(edge))

            if not isinstance(super_edge.pre_vertex,
                              AbstractProvidesNKeysForEdge):
                n_keys_map.set_n_keys_for_patitioned_edge(edge,
                                                          vertex_slice.n_atoms)
            else:
                n_keys_map.set_n_keys_for_patitioned_edge(
                    edge,
                    super_edge.pre_vertex.get_n_keys_for_partitioned_edge(
                        edge, graph_mapper))

            if isinstance(super_edge.pre_vertex,
                          AbstractProvidesOutgoingEdgeConstraints):
                edge.add_constraints(
                    super_edge.pre_vertex.get_outgoing_edge_constraints(
                        edge, graph_mapper))
            if isinstance(super_edge.post_vertex,
                          AbstractProvidesIncomingEdgeConstraints):
                edge.add_constraints(
                    super_edge.post_vertex.get_incoming_edge_constraints(
                        edge, graph_mapper))
            progress_bar.update()
        progress_bar.end()

        return {'n_keys_map': n_keys_map}

"""
EdgeToNKeysMapper
"""

# pacman imports
from pacman.model.routing_info.dict_based_partitioned_edge_n_keys_map import \
    DictBasedPartitionedEdgeNKeysMap

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
from spinn_front_end_common.utilities import exceptions


class EdgeToNKeysMapper(object):
    """
    generates a mapping between each edge and the number of keys it requires.
    """

    def __call__(self, partitioned_graph, graph_mapper, partitionable_graph):
        """
        Generate an n_keys map for the graph and add constraints
        :param partitioned_graph:
        :param graph_mapper:
        :param partitionable_graph:
        :return:
        """
        n_keys_map = DictBasedPartitionedEdgeNKeysMap()
        for vertex in partitioned_graph.subvertices:
                partitions = \
                    partitioned_graph.outgoing_edges_partitions_from_vertex(
                        vertex)
                for partition_id in partitions:
                    partition = partitions[partition_id]
                    added_constraints = False
                    for edge in partition.edges:
                        constraints = self._process_partitionable_edge(
                            edge, graph_mapper, n_keys_map, partitionable_graph,
                            partition_id)
                        if not added_constraints:
                            partition.add_constraints(constraints)
                        else:
                            self._check_constraints_equal(
                                constraints, partition.constraints)
        return {'n_keys_map': n_keys_map}

    @staticmethod
    def _check_constraints_equal(constraints, stored_constraints):
        """

        :param constraints:
        :param stored_constraints:
        :return:
        """
        for constraint in constraints:
            if constraint not in stored_constraints:
                raise exceptions.ConfigurationException(
                    "Two edges within the same partition have different "
                    "constraints. This is deemed an error. Plese fix and "
                    "try again")

    @staticmethod
    def _process_partitionable_edge(edge, graph_mapper, n_keys_map,
                                    partitionable_graph, partition_id):
        """

        :param edge:
        :param graph_mapper:
        :param n_keys_map:
        :param partitionable_graph:
        :param partition_id:
        :return:
        """
        vertex_slice = graph_mapper.get_subvertex_slice(edge.pre_subvertex)
        super_edge = \
            graph_mapper.get_partitionable_edge_from_partitioned_edge(edge)

        if not isinstance(super_edge.pre_vertex, AbstractProvidesNKeysForEdge):
            n_keys_map.set_n_keys_for_patitioned_edge(edge,
                                                      vertex_slice.n_atoms)
        else:
            n_keys_map.set_n_keys_for_patitioned_edge(
                edge,
                super_edge.pre_vertex.get_n_keys_for_partitioned_edge(
                    edge, graph_mapper))

        constraints = list()
        if isinstance(super_edge.pre_vertex,
                      AbstractProvidesOutgoingEdgeConstraints):
            constraints.extend(
                super_edge.pre_vertex.get_outgoing_edge_constraints(
                    edge, graph_mapper))
        if isinstance(super_edge.post_vertex,
                      AbstractProvidesIncomingEdgeConstraints):
            constraints.extend(
                super_edge.post_vertex.get_incoming_edge_constraints(
                    edge, graph_mapper))
        constraints.extend(
            partitionable_graph.partition_from_vertex(
                super_edge.pre_vertex, partition_id).constraints)
        return constraints

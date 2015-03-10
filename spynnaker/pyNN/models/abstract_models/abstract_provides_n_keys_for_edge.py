from six import add_metaclass
from abc import abstractmethod
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractProvidesNKeysForEdge(object):
    """ Allows a vertex to provide the number of keys for a partitioned edge,\
        rather than relying on the number of atoms in the pre-subvertex
    """

    @abstractmethod
    def get_n_keys_for_partitioned_edge(self, partitioned_edge, graph_mapper):
        """ Get the number of keys required by the given partitioned edge

        :param partitioned_edge: An edge that comes out of this vertex
        :type partitioned_edge:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :param graph_mapper: A mapper between the partitioned edge and the \
                    associated partitionable edge
        :type graph_mapper:\
                    :py:class:`pacman.model.graph_mapper.graph_mapper.GraphMapper`
        :return: A list of constraints
        :rtype: list of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        """
        pass

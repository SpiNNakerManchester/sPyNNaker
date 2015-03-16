from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractProvidesOutgoingEdgeConstraints(object):
    """ A vertex that can provide constraints for its outgoing partitioned\
        edges
    """

    @abstractmethod
    def get_outgoing_edge_constraints(self, partitioned_edge, graph_mapper):
        """ Get constraints to be added to the given edge that comes out of\
            this vertex

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

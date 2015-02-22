from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractProvidesFixedMaskVertex(object):
    """ An abstract vertex that provides its own fixed mask for routing
    """

    @abstractmethod
    def get_fixed_mask_for_partitioned_edge(self, partitioned_edge,
                                            graph_mapper):
        """ Get the fixed mask that will be used on an edge

        :param partitioned_edge: The partitioned edge down for which the mask\
                    is being provided
        :type partitioned_edge:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :param graph_mapper: A mapper between the partitioned and the \
                    associated partitionable edge
        :type graph_mapper:\
                    :py:class:`pacman.model.graph_mapper.graph_mapper.GraphMapper`
        :return: The fixed mask or None if no mask is to be fixed for this edge
        :rtype: int or None
        """
        pass

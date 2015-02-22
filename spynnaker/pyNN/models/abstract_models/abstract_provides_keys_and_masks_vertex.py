from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractProvidesKeysAndMasksVertex(object):
    """ An abstract vertex that provides its own keys and masks for
        routing
    """

    @abstractmethod
    def get_keys_and_masks_for_partitioned_edge(self, partitioned_edge,
                                                graph_mapper):
        """ Get the keys and masks that will be sent down a given
            partitioned_edge

        :param partitioned_edge: The partitioned edge down for which the keys\
                    and masks are being provided
        :type partitioned_edge:\
                    :py:class:`pacman.model.partitioned_graph.partitioned_edge.PartitionedEdge`
        :param graph_mapper: A mapper between the partitioned and the \
                    associated partitionable edge
        :type graph_mapper:\
                    :py:class:`pacman.model.graph_mapper.graph_mapper.GraphMapper`
        :return: The keys and masks to be send down the given edge
        :rtype: iterable of\
                    :py:class:`pacman.model.routing_info.key_and_mask.KeyAndMask`
        """
        pass

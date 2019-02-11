from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractFilterableEdge(object):
    """ An edge that can be filtered
    """

    __slots__ = ()

    @abstractmethod
    def filter_edge(self, graph_mapper):
        """ Determine if this edge should be filtered out

        :param graph_mapper: the mapper between graphs
        :return: True if the edge should be filtered
        :rtype: bool
        """

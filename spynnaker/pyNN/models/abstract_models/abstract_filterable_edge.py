from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractFilterableEdge(object):
    """ An edge that can be filtered
    """

    __slots__ = ()

    @abstractmethod
    def filter_edge(self, graph_mapper):
        """ method to allow edges to determine if a edge is filter-able

        :param graph_mapper: the mapper between graphs
        :rtype: bool
        """

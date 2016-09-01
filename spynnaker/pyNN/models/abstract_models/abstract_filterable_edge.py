from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractFilterableEdge(object):
    """ An edge that can be filtered
    """

    def __init__(self):
        pass

    @abstractmethod
    def filter_edge(self, graph_mapper):
        """ method to allow edges to determine if a edge is filter-able

        :param graph_mapper: the mapper between graphs
        :return: true or false
        :rtype: boolean
        :raise none: this method does not raise any known exceptions
        """

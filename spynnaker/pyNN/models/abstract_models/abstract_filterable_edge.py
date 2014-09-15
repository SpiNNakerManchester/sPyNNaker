from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractFilterableEdge(object):

    def __init__(self):
        pass

    @abstractmethod
    def filter_sub_edge(self, subedge, graph_mapper):
        """ method to allow edges to determine if a edge is filterable

        :param subedge: the subedge to be considered for filtering
        :param graph_mapper: the mapper that informs partitioned vertexes of
        their slice of atoms
        :return: true or false
        :rtype: boolean
        :raise none: this method does not raise any known exceptions
        """

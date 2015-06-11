from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractFilterableEdge(object):

    def __init__(self):
        pass

    @abstractmethod
    def filter_edge(self):
        """ Determine if the edge can be removed

        :return: True if the edge can be removed, False otherwise
        :rtype: bool
        """

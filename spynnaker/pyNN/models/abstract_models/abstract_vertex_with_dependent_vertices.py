"""
AbstractVertexWithEdgeToDependentVertices
"""

# general imports
from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractVertexWithEdgeToDependentVertices(object):
    """ A vertex with a dependent vertices, which should be connected to this
        vertex by an edge directly to each of them
    """

    def __init__(self, dependent_vertices):
        """

        :param dependent_vertices: The vertex which this vertex depends upon
        :type dependent_vertices: iterable of vertices
        :return: None
        :rtype: None
        :raise None: this method does not raise any knwon exception
        """
        self._dependent_vertices = dependent_vertices

    @property
    def dependent_vertices(self):
        """
        returns the dependent vertices which this vertex depends upon
        :return:
        """
        return self._dependent_vertices

    @abstractmethod
    def has_dependent_vertices(self):
        """
        helper method for isinstance
        :return:
        """

    @abstractmethod
    def partition_identifier_for_dependent_edge(self, dependent_edge):
        """ helper emthod for the vertex to give semantic data of the partition
        uidentifier type for each depdent vertex.

        :param dependent_edge: the edge which coems from this to one of its
        dependent vertices.
        :return: the outgoing spike parittion identifier for this depdentent edge
        """

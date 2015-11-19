# general imports
from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractVertexWithEdgeToDependentVertices(object):
    """ A vertex with a dependent vertices, which should be connected to this\
        vertex by an edge directly to each of them
    """

    def __init__(self, dependent_vertices, edge_partition_identifier):
        """

        :param dependent_vertices: The vertex which this vertex depends upon
        :type dependent_vertices: iterable of vertices
        :return: None
        :rtype: None
        :raise None: this method does not raise any known exception
        """
        self._dependent_vertices = dependent_vertices
        self._edge_partition_identifier = edge_partition_identifier

    @property
    def dependent_vertices(self):
        """ Return the vertices which this vertex depends upon
        :return:
        """
        return self._dependent_vertices

    @property
    def edge_partition_identifier_for_dependent_edge(self):
        """ Return the dependent edge identifier
        """
        return self._edge_partition_identifier

    @abstractmethod
    def has_dependent_vertices(self):
        """ Helper method for isinstance
        :return:
        """

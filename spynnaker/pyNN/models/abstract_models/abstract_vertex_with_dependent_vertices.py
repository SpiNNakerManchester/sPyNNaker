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
        return self._dependent_vertices

    @abstractmethod
    def has_dependent_vertices(self):
        pass

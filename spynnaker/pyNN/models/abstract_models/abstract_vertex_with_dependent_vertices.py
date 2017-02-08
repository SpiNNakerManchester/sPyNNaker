# general imports
from six import add_metaclass
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractVertexWithEdgeToDependentVertices(object):
    """ A vertex with a dependent vertices, which should be connected to this\
        vertex by an edge directly to each of them

        :param dependent_vertices: The vertex which this vertex depends upon
    """

    def __init__(self, dependent_vertices, edge_partition_identifier):
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

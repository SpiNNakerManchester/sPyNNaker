from .projection_application_edge import ProjectionApplicationEdge

class PyNNPartitionEdge():

    __slots__ = [
        "_pre_vertex",
        "_post_vertex",
        "_synapse_information",
        "_application_edges"]

    def __init__(self, pre_vertex, post_vertex, synapse_information):

        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._synapse_information = synapse_information
        self._application_edges = list()

        pre_app_vertices = self._pre_vertex.vertices
        post_app_vertices = self._post_vertex.vertices

        for index in range(len(pre_app_vertices)):
            self._application_edges.append(ProjectionApplicationEdge(
                pre_app_vertices[index], post_app_vertices[index], synapse_information))

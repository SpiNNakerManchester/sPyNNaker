from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from .projection_application_edge import ProjectionApplicationEdge
from spinn_front_end_common.utilities.exceptions import ConfigurationException


class PyNNPartitionEdge():

    __slots__ = [
        "_pre_vertex",
        "_post_vertex",
        "_synapse_information",
        "_application_edges",
        "_delay_edge"]

    def __init__(self, pre_vertex, post_vertex, synapse_information):

        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._synapse_information = synapse_information
        self._application_edges = list()
        self._delay_edge = None

        pre_app_vertices = self._pre_vertex.out_vertices
        post_app_vertices = self._post_vertex.in_vertices

        for index in range(len(pre_app_vertices)):
            if not isinstance(post_vertex,
                              AbstractAcceptsIncomingSynapses):
                raise ConfigurationException(
                    "postsynaptic population is not designed to receive"
                    " synaptic projections")
            self._application_edges.append(ProjectionApplicationEdge(
                pre_app_vertices[index], post_app_vertices[index], synapse_information))

    @property
    def application_edges(self):
        return self._application_edges

    @property
    def delay_edge(self):
        return self._delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge):
        self._delay_edge = delay_edge
        for edge in self._application_edges:
            edge.delay_edge = delay_edge

    @property
    def n_delay_stages(self):
        if self._delay_edge is None:
            return 0
        return self._delay_edge.pre_vertex.n_delay_stages

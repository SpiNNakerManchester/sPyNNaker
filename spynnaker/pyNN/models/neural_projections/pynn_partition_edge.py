from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses)
from .projection_application_edge import ProjectionApplicationEdge
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities import constants


class PyNNPartitionEdge():

    __slots__ = [
        "_pre_vertex",
        "_post_vertex",
        "_synapse_information",
        "_application_edges",
        "_delay_edge",
        "_label"]

    def __init__(self, pre_vertex, post_vertex, synapse_information,
                 spinnaker_control, label):

        self._pre_vertex = pre_vertex
        self._post_vertex = post_vertex
        self._synapse_information = synapse_information
        self._application_edges = list()
        self._delay_edge = None
        self._label = label

        pre_app_vertices = self._pre_vertex.out_vertices
        post_app_vertices = self._post_vertex.in_vertices
        synapse_type = synapse_information.synapse_type
        vertices_per_partition = self._post_vertex.n_incoming_partitions

        __offset = 0

        for index in range(len(pre_app_vertices)):

            partition_offset = index
            for i in range(len(vertices_per_partition)):
                if i < synapse_type:
                    partition_offset += vertices_per_partition[i]

            for dest_partition in range(len(post_app_vertices)):

                if not isinstance(post_app_vertices[dest_partition][partition_offset],
                                  AbstractAcceptsIncomingSynapses):
                    raise ConfigurationException(
                        "postsynaptic population is not designed to receive"
                        " synaptic projections")

                # check that the projection edges label is not none, and give an
                # auto generated label if set to None
                if self._label is None:
                    self._label = "projection edge {}".format(
                        spinnaker_control.none_labelled_edge_count)
                    spinnaker_control.increment_none_labelled_edge_count()
                    name = self._label
                else:
                    name = self._label + "_" + str(__offset)
                    __offset += 1

                edge_to_merge = self._find_existing_edge(
                    pre_app_vertices[index], post_app_vertices[dest_partition][partition_offset], spinnaker_control)

                if edge_to_merge is not None:
                    edge_to_merge.add_synapse_information(self._synapse_information)
                    edge = edge_to_merge
                else:
                    edge = ProjectionApplicationEdge(
                        pre_app_vertices[index], post_app_vertices[dest_partition][partition_offset], synapse_information, name)

                # add edge to the graph
                spinnaker_control.add_application_edge(edge, constants.SPIKE_PARTITION_ID)

                self._application_edges.append(edge)

    @property
    def application_edges(self):
        return self._application_edges

    @property
    def post_vertex(self):
        return self._post_vertex

    @property
    def pre_vertex(self):
        return self._pre_vertex

    @property
    def label(self):
        return self._label

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

    def _find_existing_edge(self, pre_vertex, post_vertex, spinnaker_control):
        # Find edges ending at the postsynaptic vertex
        graph_edges = spinnaker_control.original_application_graph. \
            get_edges_ending_at_vertex(post_vertex)

        # Search the edges for any that start at the presynaptic vertex
        for edge in graph_edges:
            if edge.pre_vertex == pre_vertex:
                return edge
        return None

from spynnaker.pyNN.models.abstract_models\
    .abstract_comm_models.abstract_sends_buffers_from_host_partitioned_vertex\
    import AbstractSendsBuffersFromHostPartitionedVertex

import logging
logger = logging.getLogger(__name__)


class SendsBuffersFromHostPartitionedVertexSuperVertexImpl(
        AbstractSendsBuffersFromHostPartitionedVertex):
    """ Implementation of the AbstractSendsBuffersFromHostPartitionedVertex\
        which calls a AbstractSendsBuffersFromHostPartitionableVertex\
        for the buffer details
    """

    def __init__(self, super_vertex, vertex_slice):
        """

        :param super_vertex: The super vertex that contains the information
        :type super_vertex:\
                    :py:class:`spynnaker.pyNN.models.abstract_models.abstract_comm_models.abstract_sends_buffers_from_host_partitionable_vertex.AbstractSendsBuffersFromHostPartitionableVertex`
        :param vertex_slice: The slice of the super vertex that this vertex\
                    represents
        :type vertex_slice: :py:class:`pacman.model.graph_mapper.slice.Slice`
        """
        self._super_vertex = super_vertex
        self._vertex_slice = vertex_slice

    def get_regions(self):
        return self._super_vertex.get_regions()

    def get_region_buffer_size(self, region):
        return self._super_vertex.get_region_buffer_size(region,
                                                         self._vertex_slice)

    def is_next_timestamp(self, region):
        return self._super_vertex.is_next_timestamp(region, self._vertex_slice)

    def get_next_timestamp(self, region):
        return self._super_vertex.get_next_timestamp(region,
                                                     self._vertex_slice)

    def is_next_key(self, region, timestamp):
        return self._super_vertex.is_next_key(region, self._vertex_slice,
                                              timestamp)

    def get_next_key(self, region):
        return self._super_vertex.get_next_key(region, self._vertex_slice)

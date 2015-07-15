"""
SpikeSourceArrayPartitionedVertex
"""

# pacman imports
from pacman.model.data_request_interfaces.\
    abstract_requires_routing_info_partitioned_vertex import \
    RequiresRoutingInfoPartitionedVertex
from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

# spinn front end common imports
from spinn_front_end_common.interface.buffer_management.buffer_models.\
    sends_buffers_from_host_partitioned_vertex_pre_buffered_impl \
    import SendsBuffersFromHostPartitionedVertexPreBufferedImpl


class SpikeSourceArrayPartitionedVertex(
        PartitionedVertex, RequiresRoutingInfoPartitionedVertex,
        SendsBuffersFromHostPartitionedVertexPreBufferedImpl):
    """
    SpikeSourceArrayPartitionedVertex the partitioned version of the
    spike soruce array supported by PyNN.
    """

    def __init__(self, send_buffers, resources_required, label, constraints):
        PartitionedVertex.__init__(self, resources_required, label,
                                   constraints)
        RequiresRoutingInfoPartitionedVertex.__init__(self)
        SendsBuffersFromHostPartitionedVertexPreBufferedImpl.__init__(
            self, send_buffers)
        self._base_key = None

    def set_routing_infos(self, subedge_routing_infos):
        """
        override from RequiresRoutingInfoPartitionedVertex. allows the spike
        source array to convert its neuron ids into AER id's
        :param subedge_routing_infos:
        :return:
        """
        self._base_key = subedge_routing_infos[0].keys_and_masks[0].key

    def get_next_key(self, region_id):
        """
        over ride from SendsBuffersFromHostPartitionedVertexPreBufferedImpl
        to support the fact that keys were orignally neuron-ids and need
        adjusting into keys.
        :param region_id: the regionid that contains sendable keys.
        :return:
        """
        key = SendsBuffersFromHostPartitionedVertexPreBufferedImpl\
            .get_next_key(self, region_id)
        return key | self._base_key

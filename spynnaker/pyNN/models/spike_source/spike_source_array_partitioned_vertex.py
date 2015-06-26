from spynnaker.pyNN.models.abstract_models.buffer_models\
    .sends_buffers_from_host_partitioned_vertex_pre_buffered_impl\
    import SendsBuffersFromHostPartitionedVertexPreBufferedImpl
from pacman.model.partitioned_graph.taggable_partitioned_vertex \
    import TaggablePartitionedVertex


class SpikeSourceArrayPartitionedVertex(
        TaggablePartitionedVertex,
        SendsBuffersFromHostPartitionedVertexPreBufferedImpl):

    def __init__(self, send_buffers, resources_required, label, constraints):
        TaggablePartitionedVertex.__init__(self, resources_required, label,
                                   constraints)
        SendsBuffersFromHostPartitionedVertexPreBufferedImpl.__init__(
            self, send_buffers)

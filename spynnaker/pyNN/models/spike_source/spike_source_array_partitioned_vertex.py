from spynnaker.pyNN.buffer_management.\
    sends_buffers_from_host_partitioned_vertex_pre_buffered_impl\
    import SendsBuffersFromHostPartitionedVertexPreBufferedImpl
from spinn_front_end_common.utility_models.reverse_ip_tag_multi_cast_source \
    import ReverseIpTagMultiCastSource


class SpikeSourceArrayPartitionedVertex(
        ReverseIpTagMultiCastSource,
        SendsBuffersFromHostPartitionedVertexPreBufferedImpl):

    def __init__(self, vertex_slice, machine_time_step, timescale_factor,
                 buffer_space, space_before_notification, notification_tag,
                 notification_ip_address, notification_port, board_address,
                 send_buffers, label, constraints):
        ReverseIpTagMultiCastSource(
            vertex_slice.n_atoms, machine_time_step, timescale_factor,
            port=None, label, board_address, virtual_key=None, check_key=False,
            prefix=None, prefix_type=None, tag=None, key_left_shift=0,
            sdp_port=1, buffer_space, notify_buffer_space=True,
            space_before_notification, notification_tag,
            notification_ip_address, notification_port,
            notification_strip_sdp=True, constraints, listen=False)
        SendsBuffersFromHostPartitionedVertexPreBufferedImpl.__init__(
            self, send_buffers)

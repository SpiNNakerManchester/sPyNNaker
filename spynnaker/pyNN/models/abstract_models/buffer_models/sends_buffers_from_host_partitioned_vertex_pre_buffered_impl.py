from spynnaker.pyNN.models.abstract_models.buffer_models\
    .abstract_sends_buffers_from_host_partitioned_vertex\
    import AbstractSendsBuffersFromHostPartitionedVertex

import logging
logger = logging.getLogger(__name__)


class SendsBuffersFromHostPartitionedVertexPreBufferedImpl(
        AbstractSendsBuffersFromHostPartitionedVertex):
    """ Implementation of the AbstractSendsBuffersFromHostPartitionedVertex\
        which uses an existing set of buffers for the details
    """

    def __init__(self, send_buffers):
        """

        :param send_buffers: A dictionary of the buffers of spikes to send,
                    indexed by the regions
        :type send_buffers: dict(int -> \
                    :py:class:`spinnaker.pyNN.buffer_management.storage_objects.buffered_sending_region.BufferedSendingRegion`)
        """
        self._send_buffers = send_buffers

    def get_regions(self):
        return self._send_buffers.keys()

    def get_region_buffer_size(self, region):
        return self._send_buffers[region].buffer_size

    def is_next_timestamp(self, region):
        return self._send_buffers[region].is_next_timestamp

    def get_next_timestamp(self, region):
        return self._send_buffers[region].next_timestamp

    def is_next_key(self, region, timestamp):
        return self._send_buffers[region].is_next_key(timestamp)

    def get_next_key(self, region):
        return self._send_buffers[region].next_key

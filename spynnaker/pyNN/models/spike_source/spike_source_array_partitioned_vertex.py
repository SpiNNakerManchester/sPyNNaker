from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_sends_buffers_from_host_partitioned_vertex import \
    AbstractSendsBuffersFromHostPartitionedVertex


class SpikeSourceArrayPartitionedVertex(
        AbstractSendsBuffersFromHostPartitionedVertex,
        PartitionedVertex):

    def __init__(self, buffer_collection, label, resources_used,
                 additional_constraints):
        AbstractSendsBuffersFromHostPartitionedVertex.__init__(
            self, buffer_collection)
        PartitionedVertex.__init__(self, resources_used, label,
                                   additional_constraints)

    def is_sends_buffers_from_host_partitioned_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True

    def is_buffer_sendable_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True

    def is_reverse_ip_tagable_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True

    def set_buffered_region_size(self, region_size, region_id):
        self._buffers_to_send_collection.set_size_of_region(
            region_id, region_size)

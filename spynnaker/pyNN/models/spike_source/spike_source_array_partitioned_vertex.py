from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_buffer_receivable_partitioned_vertex import \
    AbstractBufferReceivablePartitionedVertex
from spynnaker.pyNN.models.abstract_models.abstract_comm_models.abstract_buffer_sendable_partitionable_vertex import \
    AbstractBufferSendableVertex


class SpikeSourceArrayPartitionedVertex(
        AbstractBufferReceivablePartitionedVertex,
        AbstractBufferSendableVertex,
        PartitionedVertex):

    def __init__(self, buffer_collection, label, resources_used,
                 additional_constraints, tag, port, address):
        AbstractBufferReceivablePartitionedVertex.__init__(self,
                                                           buffer_collection)
        AbstractBufferSendableVertex.__init__(self, tag=tag, port=port,
                                              address=address)
        PartitionedVertex.__init__(self, resources_used, label,
                                   additional_constraints)

    def is_bufferable_receivable_partitioned_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True

    def is_buffer_sendable_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True


    def set_buffered_region_size(self, region_size, region_id):
        self._receiver_buffer_collection.set_size_of_region(region_id, region_size)



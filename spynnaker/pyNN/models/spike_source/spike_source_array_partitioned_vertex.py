from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_buffer_receivable_partitioned_vertex import \
    AbstractBufferReceivablePartitionedVertex


class SpikeSourceArrayPartitionedVertex(
        AbstractBufferReceivablePartitionedVertex, PartitionedVertex):

    def __init__(self, buffer_collection, label, resources_used, additional_constraints):
        AbstractBufferReceivablePartitionedVertex.__init__(self, buffer_collection)
        PartitionedVertex.__init__(self, resources_used, label,
                                   additional_constraints)

    def is_bufferable_receivable_partitioned_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True

    def set_region_size(self, region_size, region_id):
        self._buffer_collection.set_size_of_region(region_id, region_size)



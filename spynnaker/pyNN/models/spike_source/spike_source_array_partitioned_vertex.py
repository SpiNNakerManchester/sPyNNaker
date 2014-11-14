from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_buffer_receivable_partitioned_vertex import \
    AbstractBufferReceivablePartitionedVertex


class SpikeSourceArrayPartitionedVertex(
        AbstractBufferReceivablePartitionedVertex, PartitionedVertex):

    def __init__(self, buffers, label, resources_used, additional_constraints):
        AbstractBufferReceivablePartitionedVertex.__init__(self, buffers)
        PartitionedVertex.__init__(self, resources_used, label,
                                   additional_constraints)

    def is_bufferable_receivable_partitioned_vertex(self):
        """ helper method for is isinstance

        :return:
        """
        return True


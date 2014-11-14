from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractBufferReceivablePartitionedVertex(object):

    def __init__(self, buffers):
        self._buffers = buffers

    @abstractmethod
    def is_bufferable_receivable_partitioned_vertex(self):
        """helper method for is instance

        :return:
        """

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractBufferReceivablePartitionableVertex(object):

    def __init__(self):
        self._requires_buffering = False

    @abstractmethod
    def is_buffer_receivable_partitionable_vertex(self):
        """helper method for is instance

        :return:
        """


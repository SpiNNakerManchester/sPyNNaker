from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod

from spynnaker.pyNN.models.abstract_models.abstract_comm_models.abstract_iptagable_vertex import \
    AbstractIPTagableVertex


@add_metaclass(ABCMeta)
class AbstractSendsBuffersFromHostPartitionableVertex(AbstractIPTagableVertex):

    def __init__(self, tag, port, address):
        AbstractIPTagableVertex.__init__(self, tag=tag, port=port,
                                         address=address, strip_sdp=True)

    @abstractmethod
    def is_sends_buffers_from_host_partitionable_vertex(self):
        """helper method for is instance

        :return:
        """

    def is_ip_tagable_vertex(self):
        return True
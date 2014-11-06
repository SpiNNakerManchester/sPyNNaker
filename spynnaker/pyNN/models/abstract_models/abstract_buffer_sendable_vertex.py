from spynnaker.pyNN.models.abstract_models.abstract_iptagable_vertex import \
    AbstractIPTagableVertex
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractBufferSendableVertex(AbstractIPTagableVertex):

    def __init__(self, tag, port, address):
        AbstractIPTagableVertex.__init__(self, tag, port, address)
        self._will_send_buffers = False
        self._size_of_buffer_to_read_in_bytes = None

    @property
    def will_send_buffers(self):
        """

        :return: returns true if the vertex requires listeners to receive
        buffers during runtime
        :rtype: bool
        """
        return self._will_send_buffers

    @property
    def size_of_buffer_to_read_in_bytes(self):
        """

        :return: the size of each buffer in the core that will need to be read
        at some point during execution
        """
        return self._size_of_buffer_to_read_in_bytes

    @abstractmethod
    def is_buffer_sendable_vertex(self):
        """ helper method for is instance

        :return:
        """

    def is_ip_tagable_vertex(self):
        """ helper method for is isntance

        :return:
        """
        return True
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from spynnaker.pyNN.models.abstract_models.abstract_comm_models.\
    abstract_iptagable_vertex import AbstractIPTagableVertex


@add_metaclass(ABCMeta)
class AbstractBufferSendableVertex(AbstractIPTagableVertex):

    def __init__(self, tag, port, address):
        AbstractIPTagableVertex.__init__(self, tag=tag, port=port,
                                         address=address)
        self._will_send_buffers = False
        self._threshold_for_reporting_bytes_written = None
        self._recording_region_size_in_bytes = None

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
        return self._threshold_for_reporting_bytes_written

    def set_recording_region_size_in_bytes(self, new_value):
        """

        :param new_value:
        :return:
        """

    @abstractmethod
    def is_buffer_sendable_vertex(self):
        """ helper method for is instance

        :return:
        """

    def is_ip_tagable_vertex(self):
        return True
from collections import OrderedDict
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractBufferReceivableVertex(object):

    def __init__(self):
        self._requires_buffering = False
        self._buffers_to_transmit = OrderedDict()
        self._buffer_region_memory_size = None

    @property
    def buffer_region_memory_size(self):
        """

        :return: returns the size of the region used for buffered data
        """
        return self._buffer_region_memory_size

    @property
    def requires_buffering(self):
        """
        :return: returns true if the vertex requires buffers to be trnasmitted
        to it during runtime
        :rtype: bool
        """
        return self._requires_buffering

    @property
    def buffers_to_transmit(self):
        """ returns the list of buffers to be

        :return:
        """
        return self._buffers_to_transmit

    def received_buffer_request(self, message):
        """ method to support callback for sneding new buffers down to the
         machine

        :param message:
        :return:
        """
        ##TODO translate the message to a number of buffers to transmit
        no_buffers_requested = 1
        #send sdp message to the core in question with





    @abstractmethod
    def is_buffer_receivable_vertex(self):
        """helper method for is instance

        :return:
        """


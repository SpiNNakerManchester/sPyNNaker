import threading
import collections
import logging
from spinnman.connections.udp_packet_connections.udp_spinnaker_connection import \
    UDPSpinnakerConnection
from spinnman.messages.sdp.sdp_flag import SDPFlag

from spinnman.messages.sdp.sdp_header import SDPHeader
from spinnman.messages.sdp.sdp_message import SDPMessage
from spynnaker.pyNN.buffer_management.command_objects.event_stop_request \
    import EventStopRequest
from spynnaker.pyNN.buffer_management.command_objects.host_send_sequenced_data\
    import HostSendSequencedData
from spynnaker.pyNN.buffer_management.command_objects.start_requests \
    import StartRequests
from spynnaker.pyNN.buffer_management.command_objects.stop_requests \
    import StopRequests
from spynnaker.pyNN import exceptions


logger = logging.getLogger(__name__)


class BufferSendThread(threading.Thread):

    def __init__(self, transciever):
        threading.Thread.__init__(self)
        self._queue = collections.deque()
        self._queue_condition = threading.Condition()
        self._transciever = transciever
        self._done = False
        self._exited = False
        self.setDaemon(True)
        connections = self._transciever.get_connections()
        for connection in connections:
            if isinstance(connection, UDPSpinnakerConnection):
                self._connection = connection
                break
        if self._connection is None:
            raise  # error, no connection found

    def stop(self):
        """
        method to kill the thread
        """
        logger.debug("[_buffer send thread] Stopping")
        self._queue_condition.acquire()
        self._done = True
        self._queue_condition.notify()
        self._queue_condition.release()

        self._queue_condition.acquire()
        while not self._exited:
            self._queue_condition.wait()
        self._queue_condition.release()

    def run(self):
        """
        runs by just pulling receive requests and executing them
        """
        logger.debug("[buffer send thread] starting")
        while not self._done:
            self._queue_condition.acquire()
            while len(self._queue) == 0 and not self._done:
                print "about to wait"
                self._queue_condition.wait()
            print "finished waiting"
            request = None
            if not self._done:
                request = self._queue.pop()
            self._queue_condition.release()
            print "outside conditions", request
            if request is not None:
                self._handle_request(request)
        self._queue.append(None)
        self._queue_condition.acquire()
        self._exited = True
        self._queue_condition.notify()
        self._queue_condition.release()

    def add_request(self, request):
    #     """ adds a request to the tiger munching queue
    #
    #     :param request:
    #     :return:
    #     """
    #     self._queue_condition.acquire()
    #     self._queue.append(request)
    #     self._queue_condition.notify()
    #     self._queue_condition.release()
    #
    # def _handle_request(self, request):
        """ handles a request from the munched queue by transmitting a chunk of
        memory to a buffer

        :param request: the request container for this command message
        :return:
        """
        x, y, p = request['x'], request['y'], request['p']
        buffers = request['data']
        if isinstance(buffers, (HostSendSequencedData, StopRequests,
                                StartRequests, EventStopRequest)):
            eieio_message_as_byte_array = \
                buffers.get_eieio_message_as_byte_array()
            sdp_header = SDPHeader(destination_chip_x=x,
                                   destination_chip_y=y,
                                   destination_cpu=p,
                                   flags=SDPFlag.REPLY_NOT_EXPECTED,
                                   destination_port=1)
            sdp_message = \
                SDPMessage(sdp_header, eieio_message_as_byte_array)
            self._transciever.send_sdp_message(sdp_message)
            #self._connection.send_sdp_message(sdp_message)
        else:
            raise exceptions.ConfigurationException(
                "this type of request is not suitable for this thread. Please "
                "fix and try again")

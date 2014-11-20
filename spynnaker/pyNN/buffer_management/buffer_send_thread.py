import threading
import collections
import logging

from spynnaker.pyNN.buffer_management.storage_objects.send_data_request import \
    SendDataRequest
from spynnaker.pyNN.buffer_management.buffer_requests.stop_requests_request import \
    StopRequestsRequest
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
                self._queue_condition.wait()
            request = None
            if not self._done:
                request = self._queue.pop()
            self._queue_condition.release()
            if request is not None:
                self._handle_request(request)
        self._queue.append(None)
        self._queue_condition.acquire()
        self._exited = True
        self._queue_condition.notify()
        self._queue_condition.release()

    def add_request(self, request):
        """ adds a request to the tiger munching queue

        :param request:
        :return:
        """
        self._queue_condition.acquire()
        self._queue.append(request)
        self._queue_condition.notify()
        self._queue_condition.release()

    def _handle_request(self, request):
        """ handles a request from the munched queue by transmitting a chunk of
        memory to a buffer

        :param request:
        :return:
        """
        if isinstance(request, SendDataRequest) \
                or isinstance(request, StopRequestsRequest):
            message = request.get_eieio_command_message()
            self._transciever.send_eieio_command_message(message)
        else:
            raise exceptions.ConfigurationException(
                "this type of request is not suitable for this thread. Please "
                "fix and try again")

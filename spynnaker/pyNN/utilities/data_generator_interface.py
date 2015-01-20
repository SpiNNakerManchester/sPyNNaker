import sys
from threading import Condition


class DataGeneratorInterface(object):

    def __init__(self, associated_vertex, subvertex, placement,
                 partitioned_graph, partitionable_graph, routing_infos,
                 hostname, graph_mapper, report_default_directory,
                 progress_bar):
        self._associated_vertex = associated_vertex
        self._subvertex = subvertex
        self._placement = placement
        self._partitioned_graph = partitioned_graph
        self._partitionable_graph = partitionable_graph
        self._routing_infos = routing_infos
        self._hostname = hostname
        self._graph_mapper = graph_mapper
        self._report_default_directory = report_default_directory
        self._progress_bar = progress_bar
        self._done = False
        self._exception = None
        self._stack_trace = None
        self._wait_condition = Condition()

    def start(self):
        try:
            self._associated_vertex.generate_data_spec(
                self._subvertex, self._placement, self._partitioned_graph,
                self._partitionable_graph, self._routing_infos, self._hostname,
                self._graph_mapper, self._report_default_directory)
            self._progress_bar.update()
            self._wait_condition.acquire()
            self._done = True
            self._wait_condition.notify_all()
            self._wait_condition.release()
        except Exception as e:
            self._wait_condition.acquire()
            self._exception = e
            self._stack_trace = sys.exc_info()[2]
            self._wait_condition.notify_all()
            self._wait_condition.release()

    def wait_for_finish(self):
        self._wait_condition.acquire()
        while not self._done and self._exception is None:
            self._wait_condition.wait()
        self._wait_condition.release()
        if self._exception is not None:
            raise self._exception, None, self._stack_trace

    def __str__(self):
        return "dgi for placement {}.{}.{}".format(self._placement.x,
                                                   self._placement.y,
                                                   self._placement.p)

    def __repr__(self):
        return self.__str__()
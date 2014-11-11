import threading
import thread
import time
from visualiser_framework.visualiser_page_container import VisualiserMain
from spynnaker.pyNN.visualiser_package.visualiser_pages.configuration_page \
    import ConfigPage
import logging
logger = logging.getLogger(__name__)
import gtk


def _timeout(visualiser, timeout):
    time.sleep(timeout)
    visualiser.stop()


class VisualiserThread(threading.Thread):
    """

    """

    #sets up listeners
    def __init__(
            self, visualiser_vertex_to_page_mapping, visualiser_vertices, graph,
            visualiser, transceiver, sim_run_time, machine_time_step, subgraph,
            placements, graph_mapper, timeout=0.0, has_board=True):
        """constructor for the vis thread

        :param timeout: param for the thread
        :type timeout: int
        :return: None
        :rtype: None
        :raise None: does not raise any known exception

        """
        gtk.threads_init()
        self._has_board = has_board

        pages = list()
        #add basic machine _page
        '''machine_page = MachinePage(True, scope, machine, placements,
                                   router_tables, graph_mapper)
        pages.append(machine_page)
        #visualiser_framework.add_page(machine_page, machine_page.label)
        machine_page.show()'''
        #add configuration _page
        config_page = ConfigPage(visualiser_vertex_to_page_mapping,
                                 visualiser_vertices, graph, visualiser,
                                 transceiver, has_board, sim_run_time,
                                 machine_time_step, subgraph, placements,
                                 graph_mapper)

        config_page.add_vertex()
        other_pages = config_page.get_other_pages()
        for p in other_pages:
            pages.append(p)

        config_page.get_frame().show()
        pages.append(config_page)

        self._visulaiser_main = VisualiserMain(self, pages)
        self._visulaiser_listener = None
        threading.Thread.__init__(self)
        self._bufsize = 65536
        self._done = False
        self._port = None
        self._finish_event = threading.Event()
        self.setDaemon(True)
        if timeout > 0:
            thread.start_new_thread(_timeout, (self, timeout))

    def set_timeout(self, timeout):
        """supports changing how long to timeout

        :param timeout: the associated length of time for a timeout
        :type timeout: int
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        print("Timeout set to %f" % timeout)
        if timeout > 0:
            thread.start_new_thread(_timeout, (self, timeout))

    def set_visualiser_listener(self, listener):
        self._visulaiser_listener = listener

    def set_bufsize(self, bufsize):
        """supports changing of the _bufsize

        :param bufsize: the associated new _bufsize
        :type bufsize: int
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        self._bufsize = bufsize

    def stop(self):
        """stops the visualiser_framework thread
        :return: None
        :rtype: None
        :raise None:   does not raise any known exceptions
        """
        logger.info("[visualiser_framework] Stopping")
        self._done = True
        if self._has_board and self._visulaiser_listener is not None:
            self._visulaiser_listener.stop()

    def run(self):
        """opening method for this thread

        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        self._visulaiser_main.main()
        logger.debug("[visualiser_framework] Exiting")

    def add_page(self, page, label):
        """helper method to allow front ends to add pages to the main container

        :param page: the _page to add to the container
        :param label: the label used by the contianer to mark the _page
        :type page: a derived from abstract _page
        :type label: str
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        self._visulaiser_main.add_page(page, label)

    def add_menu_item(self, label, function_call):
        """helper method to allow front ends to add menu items to the main
        container

        :param function_call: the callback for when the menu item is clicked
        :param label: the label used by the contianer to mark the menu item
        :type function_call: a callable object
        :type label: str
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        self._visulaiser_main.add_menu_item(self, label, function_call)

    def remove_menu_item(self, label):
        """helper method to allow front ends to remove menu items to the main
           container
        :param label: the label used by the contianer to mark the menu item
        :type label: str
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        self._visulaiser_main.remove_menu_item(self, label)

    def remove_page(self, page):
        """helper method to allow front ends to remove pages to the main
           container

        :param page: the _page to add to the container
        :type page: a derived from abstract _page
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        self._visulaiser_main.remove_page(page)

    def does_page_exist(self, page):
        """helper method to check if a _page already exists
        :param page: the _page to locate in the container
        :type page: a derived from abstract _page
        :return: None
        :rtype: None
        :raise None:  does not raise any known exceptions
        """
        return self._visulaiser_main.does_page_exist(page)

    def pages(self):
        """helper method that returns the collection of pages

        :return: list of pages
        :rtype: list
        :raise None:  does not raise any known exceptions
        """
        return self._visulaiser_main.pages

# pacman imports
from spynnaker.pyNN.models.abstract_models.abstract_weight_updatable \
    import AbstractWeightUpdatable

from spinn_machine.utilities.progress_bar import ProgressBar

import logging
logger = logging.getLogger(__name__)


class GraphEdgeWeightUpdater(object):
    """ Removes graph edges that aren't required
    """

    def __call__(self, machine_graph, graph_mapper):
        """
        :param machine_graph: the machine_graph whose edges are to be updated
        :param graph_mapper: the graph mapper between graphs
        """

        # create progress bar
        progress_bar = ProgressBar(
            len(machine_graph.edges), "Updating edge weights")

        # start checking edges to decide which ones need pruning....
        for edge in machine_graph.edges:
            if isinstance(edge, AbstractWeightUpdatable):
                edge.update_weight(graph_mapper)
            progress_bar.update()
        progress_bar.end()

        # return nothing
        return machine_graph

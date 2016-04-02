# pacman imports
from spynnaker.pyNN.models.abstract_models.abstract_weight_updatable \
    import AbstractWeightUpdatable

from spinn_machine.utilities.progress_bar import ProgressBar

import logging
logger = logging.getLogger(__name__)


class GraphEdgeWeightUpdater(object):
    """ Removes graph edges that aren't required
    """

    def __call__(self, subgraph, graph_mapper):
        """
        :param subgraph: the subgraph whose edges are to be updated
        :param graph_mapper: the graph mapper between partitionable and \
                partitioned graphs.
        """

        # create progress bar
        progress_bar = ProgressBar(
            len(subgraph.subedges), "Updating edge weights")

        # start checking subedges to decide which ones need pruning....
        for subedge in subgraph.subedges:
            if isinstance(subedge, AbstractWeightUpdatable):
                subedge.update_weight(graph_mapper)
            progress_bar.update()
        progress_bar.end()

        # return nothing
        return {'subgraph': subgraph}

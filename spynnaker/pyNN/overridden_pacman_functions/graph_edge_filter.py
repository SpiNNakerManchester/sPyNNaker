from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.graph_mapper.graph_mapper \
    import GraphMapper
from pacman.utilities.progress_bar import ProgressBar
from spynnaker.pyNN.models.common.abstract_filterable_edge \
    import AbstractFilterableEdge

import logging
logger = logging.getLogger(__name__)


class GraphEdgeFilter(object):

    def __init__(self, common_report_folder):
        self._common_report_folder = common_report_folder

    def run(self, subgraph, graph_mapper):
        new_sub_graph = PartitionedGraph(label=subgraph.label)
        new_graph_mapper = GraphMapper(graph_mapper.first_graph_label,
                                       subgraph.label)

        # create progress bar
        progress_bar = \
            ProgressBar(len(subgraph.subvertices) + len(subgraph.subedges),
                        "on checking which subedges are filterable given "
                        "heuristics")

        # add the subverts directly, as they wont be pruned.
        for subvert in subgraph.subvertices:
            new_sub_graph.add_subvertex(subvert)
            associated_vertex = graph_mapper.get_vertex_from_subvertex(subvert)
            vertex_slice = graph_mapper.get_subvertex_slice(subvert)
            new_graph_mapper.add_subvertex(
                subvertex=subvert, vertex_slice=vertex_slice,
                vertex=associated_vertex)
            progress_bar.update()

        # start checking subedges to decide which ones need pruning....
        for subedge in subgraph.subedges:
            if not self._is_filterable(subedge):
                logger.debug("this subedge was not pruned {}".format(subedge))
                new_sub_graph.add_subedge(subedge)
                associated_edge = graph_mapper.\
                    get_partitionable_edge_from_partitioned_edge(subedge)
                new_graph_mapper.add_partitioned_edge(subedge, associated_edge)
            else:
                logger.debug("this subedge was pruned {}".format(subedge))
            progress_bar.update()
        progress_bar.end()

        # returned the pruned partitioned_graph and graph_mapper
        return new_sub_graph, new_graph_mapper

    def _is_filterable(self, subedge):
        if isinstance(subedge, AbstractFilterableEdge):
            return subedge.filter_sub_edge()

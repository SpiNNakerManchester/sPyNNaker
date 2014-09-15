from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.graph_mapper.graph_mapper \
    import GraphMapper
from pacman.utilities.progress_bar import ProgressBar
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge \
    import AbstractFilterableEdge


class GraphEdgeFilter(object):

    def __init__(self):
        pass

    def run(self, subgraph, graph_mapper):
        new_sub_graph = PartitionedGraph()
        new_graph_mapper = GraphMapper()

        #create progress bar
        progress_bar = \
            ProgressBar(len(subgraph.subvertices) + len(subgraph.subedges),
                        "on checking which subedges are prunable given "
                        "heuristics")

        #add the subverts directly, as they wont be pruned.
        for subvert in subgraph.subvertices:
            new_sub_graph.add_subvertex(subvert)
            associated_vertex = graph_mapper.get_vertex_from_subvertex(subvert)
            vertex_slice = graph_mapper.get_subvertex_slice(subvert)
            new_graph_mapper.add_subvertex(
                subvertex=subvert, lo_atom=vertex_slice.lo_atom,
                hi_atom=vertex_slice.hi_atom, vertex=associated_vertex)
            progress_bar.update()

        #start checking subedges to decide which ones need pruning....
        for subedge in subgraph.subedges:
            if not self._is_filterable(subedge, graph_mapper):
                new_sub_graph.add_subedge(subedge)
                associated_edge = graph_mapper.get_edge_from_subedge(subedge)
                new_graph_mapper.add_subedge(subedge, associated_edge)
                progress_bar.update()
        progress_bar.end()
        #returned the pruned partitioned_graph and graph_mapper
        return new_sub_graph, new_graph_mapper

    @staticmethod
    def _is_filterable(subedge, graph_mapper):
        associated_edge = graph_mapper.get_edge_from_subedge(subedge)
        if isinstance(associated_edge, AbstractFilterableEdge):
            return associated_edge.filter_sub_edge(subedge, graph_mapper)
        elif isinstance(associated_edge, PartitionableEdge):
            return False
        else:
            raise exceptions.FilterableException(
                "cannot figure out if subedge {} is prunable or not"
                .format(subedge))



from pacman.model.partitionable_graph.partitionable_edge import PartitionableEdge
from pacman.model.partitioned_graph.partitioned_graph import PartitionedGraph
from pacman.model.graph_mapper.graph_mapper \
    import GraphMapper
from pacman.utilities.progress_bar import ProgressBar
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_projections.delay_projection_edge\
    import DelayProjectionEdge
from spynnaker.pyNN.models.neural_projections.projection_subedge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_edge import \
    DelayAfferentPartitionableEdge


class SubgraphSubedgePruning(object):

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
            new_graph_mapper.add_subvertex(subvert, associated_vertex)
            progress_bar.update()

        #start checking subedges to decide which ones need pruning....
        for subedge in subgraph.subedges:
            if not self._is_prunable(subedge, graph_mapper):
                new_sub_graph.add_subedge(subedge)
                associated_edge = graph_mapper.get_edge_from_subedge(subedge)
                new_graph_mapper.add_subedge(subedge, associated_edge)
                progress_bar.update()
        progress_bar.end()
        #returned the pruned partitioned_graph and graph_mapper
        return new_sub_graph, new_graph_mapper

    @staticmethod
    def _is_prunable(subedge, graph_mapper):
        associated_edge = graph_mapper.get_edge_from_subedge(subedge)

        if (isinstance(associated_edge, DelayAfferentPartitionableEdge) or
                isinstance(associated_edge, DelayProjectionEdge)):
            return (subedge.pre_subvertex.lo_atom
                    != subedge.post_subvertex.lo_atom or
                    subedge.pre_subvertex.hi_atom
                    != subedge.post_subvertex.hi_atom)
        elif isinstance(subedge, ProjectionPartitionedEdge):
            return subedge.is_connected()
        elif isinstance(associated_edge, PartitionableEdge):
            return False
        else:
            raise exceptions.PrunedException(
                "cannot figure out if subedge {} is prunable or not"
                .format(subedge))



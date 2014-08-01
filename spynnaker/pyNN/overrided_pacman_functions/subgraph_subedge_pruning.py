from pacman.model.graph.edge import Edge
from pacman.model.subgraph.subgraph import Subgraph
from pacman.model.graph_subgraph_mapper.graph_subgraph_mapper \
    import GraphSubgraphMapper
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.neural_projections.projection_subedge \
    import ProjectionSubedge
from spynnaker.pyNN.models.neural_projections.delay_afferent_edge import \
    DelayAfferentEdge


class SubgraphSubedgePruning(object):

    def __init__(self):
        pass

    def run(self, subgraph, graph_to_sub_graph_mapper):
        new_sub_graph = Subgraph()
        new_graph_subgraph_mapper = GraphSubgraphMapper()

        #add the subverts directly, as they wont be pruned.
        for subvert in subgraph.subvertices:
            new_sub_graph.add_subvertex(subvert)
            associated_vertex =\
                graph_to_sub_graph_mapper.get_vertex_from_subvertex(subvert)
            new_graph_subgraph_mapper.add_subvertex(subvert, associated_vertex)

        #start checkign though subedges to decide which ones need pruning....
        for subedge in subgraph.subedges:
            if not self._is_prunable(subedge, graph_to_sub_graph_mapper):
                new_sub_graph.add_subedge(subedge)
                associated_edge = \
                    graph_to_sub_graph_mapper.get_edge_from_subedge(subedge)
                graph_to_sub_graph_mapper.add_subedge(subedge, associated_edge)
        #returned the pruned subgraph and graph_to_sub_graph_mapper
        return new_sub_graph, new_graph_subgraph_mapper

    @staticmethod
    def _is_prunable(subedge, graph_to_sub_graph_mapper):
        associated_edge = \
            graph_to_sub_graph_mapper.get_edge_from_subedge(subedge)
        if isinstance(subedge, ProjectionSubedge):
            return subedge.is_connected()
        elif isinstance(associated_edge, DelayAfferentEdge):
            return (subedge.pre_subvertex.lo_atom
                    != subedge.post_subvertex.lo_atom or
                    subedge.pre_subvertex.hi_atom
                    != subedge.post_subvertex.hi_atom)
        elif isinstance(associated_edge, Edge):
            return False
        else:
            raise exceptions.PrunedException(
                "cannot figure out if subedge {} is prunable or not"
                .format(subedge))



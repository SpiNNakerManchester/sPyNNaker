from spinn_utilities.progress_bar import ProgressBar

# pacman imports
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.graphs.machine import MachineGraph
from pacman.model.graphs.common import GraphMapper

# spynnaker imports
from spynnaker.pyNN.exceptions import FilterableException
from spynnaker.pyNN.models.abstract_models import AbstractFilterableEdge

import logging
logger = logging.getLogger(__name__)


class GraphEdgeFilter(object):
    """ Removes graph edges that aren't required
    """

    def __call__(self, machine_graph, graph_mapper):
        """
        :param machine_graph: the machine_graph whose edges are to be filtered
        :param graph_mapper: the graph mapper between graphs
        :return: a new graph mapper and machine graph
        """
        new_machine_graph = MachineGraph(label=machine_graph.label)
        new_graph_mapper = GraphMapper()

        # create progress bar
        progress = ProgressBar(
            machine_graph.n_vertices +
            machine_graph.n_outgoing_edge_partitions,
            "Filtering edges")

        # add the vertices directly, as they wont be pruned.
        for vertex in progress.over(machine_graph.vertices, False):
            self._add_vertex_to_new_graph(
                vertex, graph_mapper, new_machine_graph, new_graph_mapper)

        # start checking edges to decide which ones need pruning....
        for partition in machine_graph.outgoing_edge_partitions:
            for edge in progress.over(partition.edges, False):
                if self._is_filterable(edge, graph_mapper):
                    logger.debug("this edge was pruned %s", edge)
                    continue
                logger.debug("this edge was not pruned %s", edge)
                self._add_edge_to_new_graph(
                    edge, partition, graph_mapper, new_machine_graph,
                    new_graph_mapper)

        progress.end()
        # returned the pruned graph and graph_mapper
        return new_machine_graph, new_graph_mapper

    @staticmethod
    def _add_vertex_to_new_graph(vertex, old_mapper, new_graph, new_mapper):
        new_graph.add_vertex(vertex)
        new_mapper.add_vertex_mapping(
            machine_vertex=vertex,
            vertex_slice=old_mapper.get_slice(vertex),
            application_vertex=old_mapper.get_application_vertex(vertex))

    @staticmethod
    def _add_edge_to_new_graph(
            edge, partition, old_mapper, new_graph, new_mapper):
        new_graph.add_edge(edge, partition.identifier)
        new_mapper.add_edge_mapping(
            edge, old_mapper.get_application_edge(edge))
        # add partition constraints from the original graph to the new graph
        # add constraints from the application partition
        new_partition = new_graph.\
            get_outgoing_edge_partition_starting_at_vertex(
                edge.pre_vertex, partition.identifier)
        new_partition.add_constraints(partition.constraints)

    @staticmethod
    def _is_filterable(edge, graph_mapper):
        app_edge = graph_mapper.get_application_edge(edge)
        if isinstance(edge, AbstractFilterableEdge):
            return edge.filter_edge(graph_mapper)
        elif isinstance(app_edge, ApplicationEdge):
            return False
        raise FilterableException(
            "cannot figure out if edge {} is prunable or not".format(edge))

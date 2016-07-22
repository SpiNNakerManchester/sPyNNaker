# pacman imports
from pacman.model.graph.application.simple_application_edge \
    import SimpleApplicationEdge
from pacman.model.graph.machine.machine_graph import MachineGraph
from pacman.model.graph.graph_mapper \
    import GraphMapper
from spinn_machine.utilities.progress_bar import ProgressBar

# spynnaker imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_filterable_edge \
    import AbstractFilterableEdge

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
        new_sub_graph = MachineGraph(label=machine_graph.label)
        new_graph_mapper = GraphMapper(graph_mapper.first_graph_label,
                                       machine_graph.label)

        # create progress bar
        progress_bar = ProgressBar(
            len(machine_graph.vertices) + len(machine_graph.edges),
            "Filtering edges")

        # add the subverts directly, as they wont be pruned.
        for subvert in machine_graph.vertices:
            new_sub_graph.add_vertex(subvert)
            associated_vertex = graph_mapper.get_application_vertex(subvert)
            vertex_slice = graph_mapper.get_slice(subvert)
            new_graph_mapper.add_vertex_mapping(
                vertex=subvert, vertex_slice=vertex_slice,
                vertex=associated_vertex)
            progress_bar.update()

        # start checking edges to decide which ones need pruning....
        for subvert in machine_graph.vertices:
            out_going_partitions = \
                machine_graph.get_outgoing_edge_partitions_starting_at_vertex(
                    subvert)
            for partition in out_going_partitions:
                for subedge in partition.edges:
                    if not self._is_filterable(subedge, graph_mapper):
                        logger.debug("this subedge was not pruned {}"
                                     .format(subedge))
                        new_sub_graph.add_edge(subedge, partition.identifier)
                        associated_edge = graph_mapper.\
                            get_application_edge(
                                subedge)
                        new_graph_mapper.add_edge_mapping(
                            subedge, associated_edge)
                    else:
                        logger.debug("this subedge was pruned {}"
                                     .format(subedge))
                    progress_bar.update()
        progress_bar.end()

        # returned the pruned graph and graph_mapper
        return {'new_sub_graph': new_sub_graph,
                'new_graph_mapper': new_graph_mapper}

    @staticmethod
    def _is_filterable(subedge, graph_mapper):
        associated_edge = \
            graph_mapper.get_application_edge(subedge)
        if isinstance(subedge, AbstractFilterableEdge):
            return subedge.filter_sub_edge(graph_mapper)
        elif isinstance(associated_edge, SimpleApplicationEdge):
            return False
        else:
            raise exceptions.FilterableException(
                "cannot figure out if subedge {} is prunable or not"
                .format(subedge))

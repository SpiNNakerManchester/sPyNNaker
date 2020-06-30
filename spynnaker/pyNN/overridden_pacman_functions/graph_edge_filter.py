# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.graphs.machine import MachineGraph
from spynnaker.pyNN.exceptions import FilterableException
from spynnaker.pyNN.models.abstract_models import AbstractFilterableEdge

logger = FormatAdapter(logging.getLogger(__name__))


class GraphEdgeFilter(object):
    """ Removes graph edges that aren't required
    """

    def __call__(self, app_graph, machine_graph):
        """
        :param app_graph: The application graph
        :type app_graph:
            ~pacman.model.graphs.application.ApplicationGraph or None
        :param ~.MachineGraph machine_graph:
             The machine_graph whose edges are to be filtered
        :return: a new, filtered machine graph
        :rtype: ~.MachineGraph
        """
        new_machine_graph = MachineGraph(
            label=machine_graph.label, application_graph=app_graph)

        # create progress bar
        progress = ProgressBar(
            machine_graph.n_vertices +
            machine_graph.n_outgoing_edge_partitions,
            "Filtering edges")

        # add the vertices directly, as they won't be pruned.
        for vertex in progress.over(machine_graph.vertices, False):
            new_machine_graph.add_vertex(vertex)
            vertex.associate_application_vertex()

        # start checking edges to decide which ones need pruning....
        prune_count = 0
        no_prune_count = 0
        for partition in progress.over(machine_graph.outgoing_edge_partitions):
            for edge in partition.edges:
                if self._is_filterable(edge):
                    logger.debug("this edge was pruned {}", edge)
                    prune_count += 1
                    continue
                logger.debug("this edge was not pruned {}", edge)
                no_prune_count += 1
                self._add_edge_to_new_graph(edge, partition, new_machine_graph)

        # return the pruned graph after remembering that it is the graph that
        # the application graph maps to now
        logger.debug("prune_count:{} no_prune_count:{}",
                     prune_count, no_prune_count)
        return new_machine_graph

    @staticmethod
    def _add_edge_to_new_graph(edge, partition, new_graph):
        """
        :param ~.MachineEdge edge:
        :param ~.OutgoingEdgePartition partition:
        :param ~.MachineGraph new_graph:
        """
        new_graph.add_edge(edge, partition.identifier)
        edge.associate_application_edge()

        # add partition constraints from the original graph to the new graph
        # add constraints from the application partition
        new_partition = new_graph. \
            get_outgoing_edge_partition_starting_at_vertex(
                edge.pre_vertex, partition.identifier)
        new_partition.add_constraints(partition.constraints)

    @staticmethod
    def _is_filterable(edge):
        """
        :param ~.MachineEdge edge:
        :rtype: bool
        """
        # If our associated application edge wants to say don't filter...
        if (isinstance(edge.app_edge, AbstractFilterableEdge)
                and not edge.app_edge.filter_edge()):
            return False
        if isinstance(edge, AbstractFilterableEdge):
            return edge.filter_edge()
        elif isinstance(edge.app_edge, ApplicationEdge):
            return False
        raise FilterableException(
            "cannot figure out if edge {} is prunable or not".format(edge))

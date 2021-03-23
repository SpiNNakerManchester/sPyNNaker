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

import os
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge


class SpYNNakerNeuronGraphNetworkSpecificationReport(object):
    """ Produces a report describing the graph created from the neural \
        populations and projections.
    """

    _GRAPH_TITLE = "The graph of the network in graphical form"
    _GRAPH_NAME = "network_graph.gv"
    _NODE_LABEL = "{} ({} neurons)"

    @staticmethod
    def _get_diagram(label):
        """
        :param str label:
        :rtype: ~graphviz.Digraph
        """
        # pylint: disable=import-error
        try:
            import graphviz
        except ImportError as e:
            raise SpynnakerException(
                "graphviz is required to use this report. "
                "Please install graphviz if you want to use this report."
                ) from e
        return graphviz.Digraph(comment=label)

    def __call__(self, report_folder, application_graph):
        """
        :param str report_folder: the report folder to put figure into
        :param ~pacman.model.graphs.application.ApplicationGraph \
                application_graph:
            the app graph
        """
        # create holders for data
        dot_diagram = self._get_diagram(self._GRAPH_TITLE)

        # build progress bar for the vertices, edges, and rendering
        progress = ProgressBar(
            application_graph.n_vertices +
            application_graph.n_outgoing_edge_partitions + 1,
            "generating the graphical representation of the neural network")

        # write vertices into dot diagram
        vertex_ids = self._generate_vertices(
            application_graph, dot_diagram, progress)
        # write edges into dot diagram
        self._generate_edges(
            application_graph, dot_diagram, vertex_ids, progress)

        # write dot file and generate pdf
        file_to_output = os.path.join(report_folder, self._GRAPH_NAME)
        dot_diagram.render(file_to_output, view=False)
        progress.update()
        progress.end()

    @classmethod
    def _generate_vertices(cls, graph, dot_diagram, progress):
        """
        :param ~.ApplicationGraph graph:
        :param ~graphviz.Digraph dot_diagram:
        :param ~.ProgressBar progress:
        :rtype: dict(~.ApplicationVertex,str)
        """
        vertex_ids = dict()
        for vertex_counter, vertex in progress.over(
                enumerate(graph.vertices), False):
            # Arbitrary labels used inside dot
            vertex_id = str(vertex_counter)
            dot_diagram.node(
                vertex_id,
                cls._NODE_LABEL.format(vertex.label, vertex.n_atoms))
            vertex_ids[vertex] = vertex_id
        return vertex_ids

    @staticmethod
    def _generate_edges(graph, dot_diagram, vertex_ids, progress):
        """
        :param ~.ApplicationGraph graph:
        :param ~graphviz.Digraph dot_diagram:
        :param dict(~.ApplicationVertex,str) vertex_ids:
        :param ~.ProgressBar progress:
        """
        for partition in progress.over(graph.outgoing_edge_partitions, False):
            for edge in partition.edges:
                source_vertex_id = vertex_ids[edge.pre_vertex]
                dest_vertex_id = vertex_ids[edge.post_vertex]
                if isinstance(edge, ProjectionApplicationEdge):
                    for synapse_info in edge.synapse_information:
                        dot_diagram.edge(
                            source_vertex_id, dest_vertex_id,
                            str(synapse_info.connector))
                else:
                    # Unlabelled edge
                    dot_diagram.edge(source_vertex_id, dest_vertex_id)

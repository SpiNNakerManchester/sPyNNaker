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
import os
from spinn_utilities.config_holder import get_config_str
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
logger = FormatAdapter(logging.getLogger(__name__))

CUTOFF = 100
_GRAPH_TITLE = "The graph of the network in graphical form"
_GRAPH_NAME = "network_graph.gv"
_NODE_LABEL = "{} ({} neurons)"
_GRAPH_FORMAT = "png"


def _get_diagram(label):
    """
    :param str label:
    :rtype: tuple(~graphviz.Digraph, type)
    """
    # pylint: disable=import-error
    try:
        import graphviz
    except ImportError as e:
        raise SpynnakerException(
            "graphviz is required to use this report. "
            "Please install graphviz if you want to use this report."
            ) from e
    return (graphviz.Digraph(comment=label),
            graphviz.backend.ExecutableNotFound)


def spynnaker_neuron_graph_network_specification_report():
    """
    Produces a report describing the graph created from the neural \
        populations and projections.

    :param str report_folder: the report folder to put figure into
    """
    # create holders for data
    view = SpynnakerDataView()
    application_graph = view.runtime_graph
    dot_diagram, exeNotFoundExn = _get_diagram(_GRAPH_TITLE)

    graph_format = get_config_str("Reports", "network_graph_format")
    if graph_format is None:
        if (application_graph.n_vertices +
                application_graph.n_outgoing_edge_partitions) > CUTOFF:
            logger.warning(
                "cfg write_network_graph ignored as network_graph_format "
                "is None and the network is big")
            return
        else:
            graph_format = _GRAPH_FORMAT
    # build progress bar for the vertices, edges, and rendering
    progress = ProgressBar(
        application_graph.n_vertices +
        application_graph.n_outgoing_edge_partitions + 1,
        "generating the graphical representation of the neural network")

    # write vertices into dot diagram
    vertex_ids = _generate_vertices(
        application_graph, dot_diagram, progress)
    # write edges into dot diagram
    _generate_edges(
        application_graph, dot_diagram, vertex_ids, progress)

    # write dot file and generate pdf
    file_to_output = os.path.join(view.run_dir_path, _GRAPH_NAME)
    try:
        dot_diagram.render(file_to_output, view=False, format=graph_format)
    except exeNotFoundExn:
        logger.exception("could not render diagram in {}", file_to_output)
    progress.update()
    progress.end()


def _generate_vertices(graph, dot_diagram, progress):
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
            vertex_id, _NODE_LABEL.format(vertex.label, vertex.n_atoms))
        vertex_ids[vertex] = vertex_id
    return vertex_ids


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

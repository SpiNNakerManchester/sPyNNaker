# Copyright (c) 2016 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
import logging
from typing import Dict, Set, Tuple, Type, TypeVar, TYPE_CHECKING

from spinn_utilities.config_holder import (
    get_config_str_or_none, get_report_path)
from spinn_utilities.log import FormatAdapter
from spinn_utilities.progress_bar import ProgressBar
from pacman.model.graphs.application import ApplicationVertex
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
if TYPE_CHECKING:
    import graphviz as gv  # type: ignore[import]

logger = FormatAdapter(logging.getLogger(__name__))
_RE = TypeVar("_RE", bound=RuntimeError)

CUTOFF = 100
_GRAPH_TITLE = "The graph of the network in graphical form"
_GRAPH_FORMAT = "png"


def _get_diagram(label: str) -> Tuple[gv.Digraph, Type[gv.ExecutableNotFound]]:
    # pylint: disable=import-error,import-outside-toplevel
    try:
        import graphviz
    except ImportError as e:
        raise SpynnakerException(
            "graphviz is required to use this report. "
            "Please install graphviz if you want to use this report."
            ) from e
    return (graphviz.Digraph(comment=label),
            graphviz.ExecutableNotFound)


def spynnaker_neuron_graph_network_specification_report() -> None:
    """
    Produces a report describing the graph created from the neural
    populations and projections.
    """
    # create holders for data
    dot_diagram, exe_not_found_exn = _get_diagram(_GRAPH_TITLE)

    graph_format = get_config_str_or_none("Reports", "network_graph_format")
    if graph_format is None:
        graph_format = _GRAPH_FORMAT
        if (SpynnakerDataView.get_n_vertices() +
                SpynnakerDataView.get_n_partitions()) > CUTOFF:
            logger.warning(
                "cfg write_network_graph ignored as network_graph_format "
                "is None and the network is big")
            return
    # build progress bar for the vertices, edges, and rendering
    progress = ProgressBar(
        SpynnakerDataView.get_n_vertices() +
        SpynnakerDataView.get_n_partitions(),
        "generating the graphical representation of the neural network")

    # write vertices into dot diagram
    vertex_ids = _generate_vertices(dot_diagram, progress)
    # write edges into dot diagram
    _generate_edges(dot_diagram, vertex_ids, progress)

    # write dot file and generate PDF
    file_to_output = get_report_path("path_network_graph")

    logger.info(f"rendering dot diagram {file_to_output}")
    try:
        dot_diagram.render(file_to_output, view=False, format=graph_format)
    except exe_not_found_exn:
        logger.exception("could not render diagram in {}", file_to_output)
    finally:
        progress.end()


def _generate_vertices(
        dot_diagram: gv.Digraph,
        progress: ProgressBar) -> Dict[ApplicationVertex, str]:
    """
    :return: the mapping from vertex to ID for the generated vertices
    """
    vertex_ids: Dict[ApplicationVertex, str] = dict()
    for vertex_counter, vertex in progress.over(
            enumerate(SpynnakerDataView.iterate_vertices()), False):
        # Arbitrary labels used inside dot
        vertex_id = str(vertex_counter)
        dot_diagram.node(
            vertex_id, f"{vertex.label} ({vertex.n_atoms} neurons)")
        vertex_ids[vertex] = vertex_id
    return vertex_ids


def _generate_edges(
        dot_diagram: gv.Digraph, vertex_ids: Dict[ApplicationVertex, str],
        progress: ProgressBar) -> None:
    for partition in progress.over(
            SpynnakerDataView.iterate_partitions(), False):
        for edge in partition.edges:
            source_vertex_id = vertex_ids[edge.pre_vertex]
            dest_vertex_id = vertex_ids[edge.post_vertex]
            if isinstance(edge, ProjectionApplicationEdge):
                links: Set[str] = set()
                for synapse_info in edge.synapse_information:
                    links.add(str(synapse_info.connector))
                for synapse_str in links:
                    dot_diagram.edge(
                        source_vertex_id, dest_vertex_id, synapse_str)
            else:
                # Unlabelled edge
                dot_diagram.edge(source_vertex_id, dest_vertex_id)

import logging
import os

from spinn_utilities.progress_bar import ProgressBar
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge

logger = logging.getLogger(__name__)


class SpYNNakerNeuronGraphNetworkSpecificationReport(object):
    """
    """

    @staticmethod
    def _get_diagram(label):
        # pylint: disable=import-error
        try:
            import graphviz  # @UnresolvedImport
        except Exception:
            raise SpynnakerException(
                "graphviz is required to use this report.  "
                "Please install graphviz if you want to use this report.")
        return graphviz.Digraph(comment=label)

    def __call__(self, report_folder, application_graph):
        """
        :param report_folder: the report folder to put figure into
        :param application_graph: the app graph
        :rtype: None
        """

        # create holders for data
        vertex_holders = dict()
        dot_diagram = self._get_diagram(
            "The graph of the network in graphical form")

        # build progress bar for the vertices, edges, and rendering
        progress = ProgressBar(
            application_graph.n_vertices +
            application_graph.n_outgoing_edge_partitions + 1,
            "generating the graphical representation of the neural network")

        # write vertices into dot diagram
        for vertex_counter, vertex in progress.over(
                enumerate(application_graph.vertices), False):
            dot_diagram.node(
                "{}".format(vertex_counter),
                "{} ({} neurons)".format(vertex.label, vertex.n_atoms))
            vertex_holders[vertex] = vertex_counter

        # write edges into dot diagram
        for partition in progress.over(
                application_graph.outgoing_edge_partitions, False):
            for edge in partition.edges:
                source_vertex_id = vertex_holders[edge.pre_vertex]
                dest_vertex_id = vertex_holders[edge.post_vertex]
                if isinstance(edge, ProjectionApplicationEdge):
                    for synapse_info in edge.synapse_information:
                        dot_diagram.edge(
                            "{}".format(source_vertex_id),
                            "{}".format(dest_vertex_id),
                            "{}".format(synapse_info.connector))
                else:
                    dot_diagram.edge(
                        "{}".format(source_vertex_id),
                        "{}".format(dest_vertex_id))

        # write dot file and generate pdf
        file_to_output = os.path.join(report_folder, "network_graph.gv")
        dot_diagram.render(file_to_output, view=False)
        progress.update()
        progress.end()

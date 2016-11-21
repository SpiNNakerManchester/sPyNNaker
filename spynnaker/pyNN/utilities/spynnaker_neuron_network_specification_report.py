import logging
import graphviz
import os

logger = logging.getLogger(__name__)


class SpYNNakerNeuronGraphNetworkSpecificationReport(object):
    """
    """

    def __call__(self, report_folder, application_graph, connection_holder):
        """

        :param report_folder:
        :param application_graph:
        :param connection_holder:
        :return:
        """

        vertex_holders = dict()

        dot_diagram = graphviz.Digraph(
            comment="The graph of the network in graphical form")

        vertex_counter = 0
        for vertex in application_graph.vertices:
            for atom in range(0, vertex.n_atoms):
                dot_diagram.node(
                    "{}:{}".format(vertex_counter, atom),
                    "atom {} of {}".format(atom, vertex.label))
                vertex_holders[vertex] = vertex_counter
            vertex_counter += 1

        for edge in connection_holder.keys():
            connection_holder = connection_holder[edge]
            for (source, destination, _, _) in connection_holder:
                source_vertex_id = vertex_holders[edge.pre_vertex]
                dest_vertex_id = vertex_holders[edge.post_vertex]
                dot_diagram.edge(
                    "{}:{}".format(source_vertex_id, source),
                    "{}:{}".format(dest_vertex_id, destination))

        file_to_output = os.path.join(report_folder, "visual_graph.gv")
        dot_diagram.render(file_to_output, view=True)
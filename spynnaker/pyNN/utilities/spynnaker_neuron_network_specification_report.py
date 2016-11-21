import logging
import graphviz
import os
from spinn_machine.utilities.progress_bar import ProgressBar
from spynnaker.pyNN import exceptions

logger = logging.getLogger(__name__)


class SpYNNakerNeuronGraphNetworkSpecificationReport(object):
    """
    """

    def __call__(self, report_folder, application_graph, connection_holder,
                 dsg_targets):
        """

        :param report_folder: the report folder to put figure into
        :param application_graph: the app graph
        :param connection_holder: the set of connection holders
        :param dsg_targets: the dsg to ensure dsg has been executed
        :return: None
        """

        # verify that the dsg has been exeucted
        if dsg_targets is None:
            raise exceptions.SynapticConfigurationException(
                "dsg targets should not be none, used as a check for "
                "connection holder data to be generated")

        # create holders for data
        vertex_holders = dict()
        dot_diagram = graphviz.Digraph(
            comment="The graph of the network in graphical form")

        # build prgress bar for the vertices, edges, and rendering
        progress_bar = ProgressBar(
            len(application_graph.vertices) +
            len(connection_holder.keys()) + 1,
            "generating the graphical representation of the neural network")

        # write vertices into dot diagram
        vertex_counter = 0
        for vertex in application_graph.vertices:
            for atom in range(0, vertex.n_atoms):
                dot_diagram.node(
                    "{}_{}".format(vertex_counter, atom),
                    "atom {} of {}".format(atom, vertex.label))
                vertex_holders[vertex] = vertex_counter
            vertex_counter += 1
            progress_bar.update()

        # write edges into dot diagram
        for edge, synapse_information in connection_holder.keys():
                this_connection_holder = \
                    connection_holder[(edge, synapse_information)]
                for (source, destination, _, _) in this_connection_holder:
                    source_vertex_id = vertex_holders[edge.pre_vertex]
                    dest_vertex_id = vertex_holders[edge.post_vertex]
                    dot_diagram.edge(
                        "{}_{}".format(source_vertex_id, source),
                        "{}_{}".format(dest_vertex_id, destination))
                progress_bar.update()

        # write dot file and generate pdf
        file_to_output = os.path.join(report_folder, "visual_graph.gv")
        dot_diagram.render(file_to_output, view=False)
        progress_bar.update()
        progress_bar.end()

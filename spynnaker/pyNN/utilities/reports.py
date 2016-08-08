import logging
import os
from spinn_machine.utilities.progress_bar import ProgressBar

from spynnaker.pyNN import exceptions, ProjectionPartitionableEdge
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder

logger = logging.getLogger(__name__)


def generate_synaptic_matrix_reports(
        common_report_directory, partitionable_graph, partitioned_graph,
        placements, txrx, routing_infos, graph_mapper,
        loaded_application_data_token):
    """converts synaptic matrix for every partitionable edge.

    :param loaded_application_data_token: needs to be done after loaded
    :param routing_infos: routing infos
    :param placements: placements
    :param txrx: the spinnman instance
    :param partitionable_graph: the application graph
    :param common_report_directory: the location for these reports
    :param partitioned_graph: the machine graph
    :param graph_mapper: the mapping between app and machine graphs.
    :return: None
    """

    if not loaded_application_data_token:
        raise exceptions.SpynnakerException("Haven't loaded the app data yet.")

    top_level_folder = os.path.join(common_report_directory,
                                    "synaptic_matrix_reports")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    for partitionable_edge in partitionable_graph.edges:

        if isinstance(partitionable_edge, ProjectionPartitionableEdge):
            file_name = os.path.join(
                top_level_folder, "synaptic_matrix_for_partitionable_edge_{}"
                                  .format(partitionable_edge))
            output = None
            try:
                output = open(file_name, "w")
            except IOError:
                logger.error("Generate_placement_reports: Can't open file"
                             " {} for writing.".format(file_name))

            connection_holder = ConnectionHolder(
                None, True, partitionable_edge.pre_vertex.n_atoms,
                partitionable_edge.post_vertex.n_atoms)

            subedges = graph_mapper.\
                get_partitioned_edges_from_partitionable_edge(
                    partitionable_edge)

            progress = ProgressBar(
                len(subedges),
                "Getting synaptic matrix for projection between {} and {}"
                .format(
                    partitionable_edge.pre_vertex.label,
                    partitionable_edge.post_vertex.label))

            for subedge in subedges:
                placement = placements.get_placement_of_subvertex(
                    subedge.post_subvertex)
                connections = partitionable_edge.post_vertex.\
                    get_connections_from_machine(
                        txrx, placement, subedge, graph_mapper, routing_infos,
                        partitionable_edge.synapse_information[0],
                    partitioned_graph)
                if connections is not None:
                    connection_holder.add_connections(connections)
                progress.update()
            progress.end()
            connection_holder.finish()

            output.write("{}".format(connection_holder))

            output.flush()
            output.close()
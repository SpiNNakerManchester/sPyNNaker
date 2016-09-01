import logging
import os
from spinn_machine.utilities.progress_bar import ProgressBar

from spynnaker.pyNN import exceptions, ProjectionApplicationEdge
from spynnaker.pyNN.models.neuron.connection_holder import ConnectionHolder

logger = logging.getLogger(__name__)


def generate_synaptic_matrix_reports(
        common_report_directory, application_graph, machine_graph,
        placements, txrx, routing_infos, graph_mapper,
        loaded_application_data_token, machine_time_step):
    """converts synaptic matrix for every partitionable edge.

    :param loaded_application_data_token: needs to be done after loaded
    :param routing_infos: routing information
    :param placements: placements
    :param txrx: the spinnman instance
    :param application_graph: the application graph
    :param common_report_directory: the location for these reports
    :param machine_graph: the machine graph
    :param graph_mapper: the mapping between app and machine graphs.
    :return: None
    """

    if not loaded_application_data_token:
        raise exceptions.SpynnakerException("Haven't loaded the app data yet.")

    top_level_folder = os.path.join(common_report_directory,
                                    "synaptic_matrix_reports")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    for application_edge in application_graph.edges:

        if isinstance(application_edge, ProjectionApplicationEdge):
            file_name = os.path.join(
                top_level_folder, "synaptic_matrix_for_partitionable_edge_{}"
                                  .format(application_edge))
            output = None
            try:
                output = open(file_name, "w")
            except IOError:
                logger.error("Generate_placement_reports: Can't open file"
                             " {} for writing.".format(file_name))

            connection_holder = ConnectionHolder(
                None, True, application_edge.pre_vertex.n_atoms,
                application_edge.post_vertex.n_atoms)

            machine_edges = graph_mapper.get_machine_edges(application_edge)

            progress = ProgressBar(
                len(machine_edges),
                "Getting synaptic matrix for projection between {} and {}"
                .format(
                    application_edge.pre_vertex.label,
                    application_edge.post_vertex.label))

            for machine_edge in machine_edges:
                placement = placements.get_placement_of_vertex(
                    machine_edge.post_vertex)
                connections = application_edge.post_vertex.\
                    get_connections_from_machine(
                        txrx, placement, machine_edge, graph_mapper,
                        routing_infos, application_edge.synapse_information[0],
                        machine_time_step)
                if connections is not None:
                    connection_holder.add_connections(connections)
                progress.update()
            progress.end()
            connection_holder.finish()

            output.write("{}".format(connection_holder))

            output.flush()
            output.close()

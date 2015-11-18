import logging
import os

logger = logging.getLogger(__name__)


def generate_synaptic_matrix_reports(common_report_directory,
                                     partitioned_graph, graph_mapper):
    """

    :param common_report_directory:
    :param partitioned_graph:
    :param graph_mapper:
    :return:
    """
    top_level_folder = os.path.join(common_report_directory,
                                    "synaptic_matrix_reports")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    for partitioned_edge in partitioned_graph.subedges():
        file_name = os.path.join(top_level_folder,
                                 "synaptic_matrix_for_patitioned_edge_{}"
                                 .format(partitioned_edge))
        output = None
        try:
            output = open(file_name, "w")
        except IOError:
            logger.error("Generate_placement_reports: Can't open file"
                         " {} for writing.".format(file_name))

        # extract matrix
        synaptic_matrix = partitioned_edge.get_synapse_sublist(graph_mapper)
        counter = 0
        for synaptic_row in synaptic_matrix.get_rows():
            output_string = "entry {} [ \n target_index[".format(counter)
            for target in synaptic_row.target_indices:
                output_string += str(target) + ", "
            output_string += "] \n"
            output_string += "weights["
            for weight in synaptic_row.weights:
                output_string += str(weight) + ", "
            output_string += "] \n"
            output_string += "delays["
            for delay in synaptic_row.delays:
                output_string += str(delay) + ", "
            output_string += "] \n"
            output_string += "types["
            for synapse_type in synaptic_row.synapse_types:
                output_string += str(synapse_type) + ", "
            output_string += "] \n ] \n"
            output.write(output_string)
            counter += 1
        output.flush()
        output.close()


def generate_synaptic_matrix_report(common_report_directory, partitioned_edge):
    """

    :param common_report_directory:
    :param partitioned_edge:
    :return:
    """
    top_level_folder = os.path.join(common_report_directory,
                                    "synaptic_matrix_reports")
    if not os.path.exists(top_level_folder):
        os.mkdir(top_level_folder)
    file_name = os.path.join(top_level_folder,
                             "synaptic_matrix_for_patitioned_edge_{}"
                             .format(partitioned_edge))
    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file"
                     " {} for writing.".format(file_name))

    # extract matrix
    synaptic_matrix = partitioned_edge.synapse_sublist
    counter = 0
    for synaptic_row in synaptic_matrix.get_rows():
        output_string = "entry {} [ \n target_index[".format(counter)
        for target in synaptic_row.target_indices:
            output_string += str(target) + ", "
        output_string += "] \n"
        output_string += "weights["
        for weight in synaptic_row.weights:
            output_string += str(weight) + ", "
        output_string += "] \n"
        output_string += "delays["
        for delay in synaptic_row.delays:
            output_string += str(delay) + ", "
        output_string += "] \n"
        output_string += "types["
        for synapse_type in synaptic_row.synapse_types:
            output_string += str(synapse_type) + ", "
        output_string += "] \n ] \n"
        output.write(output_string)
        counter += 1
    output.flush()
    output.close()

import logging
import os
import ntpath
import pickle
import time

logger = logging.getLogger(__name__)


def generate_synaptic_matrix_reports(common_report_directory,
                                     partitioned_graph, graph_mapper):
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
        #extract matrix
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
    #extract matrix
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


def write_memory_map_report(report_default_directory,
                            processor_to_app_data_base_address):
    file_name = os.path.join(report_default_directory,
                             "memory_map_from_processor_to_address_space")
    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file"
                     " {} for writing.".format(file_name))

    for key in processor_to_app_data_base_address.keys():
        output.write(str(key) + ": ")
        data = processor_to_app_data_base_address[key]
        output.write(
            "{}: ('start_address': {}, hex({}), 'memory_used': {}, "
            "'memory_written': {} \n".format(
                key, data['start_address'], hex(data['start_address']),
                data['memory_used'], data['memory_written']))
    output.flush()
    output.close()


def generate_synaptic_matrix_report_from_dat_file(
        common_report_directory, application_generated_data_files_directory,
        partitioned_graph):
    pass


def network_specification_report(report_folder, graph, hostname):
    """
    Generate report on the user's network specification.
    """
    filename = report_folder + os.sep + "network_specification.rpt"
    f_network_specification = None
    try:
        f_network_specification = open(filename, "w")
    except IOError:
        logger.error("Generate_placement_reports: Can't open file {}"
                     " for writing.".format(filename))

    f_network_specification.write("        Network Specification\n")
    f_network_specification.write(" =====================\n\n")
    time_date_string = time.strftime("%c")
    f_network_specification.write("Generated: {}".format(time_date_string))
    f_network_specification.write(" for target machine '{}'".format(hostname))
    f_network_specification.write("\n\n")
    # Print information on vertices:
    f_network_specification.write("*** Vertices:\n")
    for vertex in graph.vertices:
        label = vertex.label
        model = vertex.model_name
        size = vertex.n_atoms
        #params = vertex.parameters
        constraints = vertex.constraints
        f_network_specification.write("AbstractConstrainedVertex {}, size: {}\n"
                                      .format(label, size))
        f_network_specification.write("Model: {}\n".format(model))
        for constraint in constraints:
            constraint_str = constraint.label
            f_network_specification.write("constraint: {}\n"
                                          .format(constraint_str))
        #if params is None or len(params.keys()) == 0:
        #    f_network_specification.write("  Parameters: None\n\n")
        #else:
        #    f_network_specification.write("  Parameters: %s\n\n" % params)
        f_network_specification.write("\n")

    # Print information on edges:
    f_network_specification.write("*** Edges:\n")
    for edge in graph.edges:
        label = edge.label
        model = "No Model"
        if hasattr(edge, "connector"):
            model = edge.connector.__class__.__name__
        pre_v = edge.pre_vertex
        post_v = edge.post_vertex
        pre_v_sz = pre_v.n_atoms
        post_v_sz = post_v.n_atoms
        pre_v_label = pre_v.label
        post_v_label = post_v.label
        edge_str = "PartitionableEdge {} from vertex: '{}' ({} atoms) to vertex: '{}' " \
                   "({} atoms)\n".format(label, pre_v_label, pre_v_sz,
                                         post_v_label, post_v_sz)
        f_network_specification.write(edge_str)
        f_network_specification.write("  Model: {}\n".format(model))
        #if params is None or len(params.keys()) == 0:
        #    f_network_specification.write("  Parameters: None\n\n")
        #else:
        #    f_network_specification.write("  Parameters: %s\n\n" % params)
        f_network_specification.write("\n")
    # Close file:
    f_network_specification.close()


def start_transceiver_rerun_script(report_directory, hostname, board_version):
    """Generate the start of the rerun script (settign up trnasciever and such)

    :param report_directory: the directroy to which reports are stored
    :type report_directory: str
    :return None
    :rtype: None
    :raise IOError: when a file cannot be opened for some reason
    """
    file_name = report_directory + os.sep + "rerun_script.py"
    output = None
    try:
        output = open(file_name, "w")
    except IOError:
        logger.error("Generate_rerun_script: Can't open file {} for "
                     "writing.".format(file_name))
    output.write("from spinnman.transceiver import "
                 "create_transceiver_from_hostname\n\n")
    output.write("from spinnman.data.file_data_reader import FileDataReader as"
                 " SpinnmanFileDataReader \n\n")
    output.write("from spynnaker.pyNN.spynnaker_comms_functions import "
                 "SpynnakerCommsFunctions \n \n")
    output.write("import pickle \n\n")
    output.write("txrx = create_transceiver_from_hostname(hostname=\"{}\", "
                 "discover=False)\n\n".format(hostname))
    output.write("txrx.ensure_board_is_ready(int({})) \n\n".format(board_version))
    output.write("txrx.discover_connections() \n \n")
    output.close()


def _append_to_rerun_script(report_directory, appended_strings):
    """helper method to add stuff to the rerun python script

    :param report_directory: the directory to which the reload script is stored\
     in
    :param appended_strings: the iterable list of strings where each string is a\
    command in string form
    :type report_directory: str
    :type appended_strings: iterable str
    :return: None
    :rtype: None
    :raise IOError: when a file cannot be opened for some reason
    """
    file_name = report_directory + os.sep + "rerun_script.py"
    output = None
    try:
        output = open(file_name, "a")
    except IOError:
        logger.error("Generate_rerun_script: Can't open file {} for "
                     "writing.".format(file_name))

    for line in appended_strings:
        output.write(line + "\n")
    output.close()


def re_load_script_application_data_load(
        file_path_for_application_data, placement, start_address,
        memory_written, user_o_register_address, binary_folder):
    lines = list()
    lines.append("application_data_file_reader = "
                 "SpinnmanFileDataReader(\"{}\")"
                 .format(ntpath.basename(
                 file_path_for_application_data)))

    lines.append("txrx.write_memory({}, {}, {}, application_data_file_reader,"
                 " {})".format(placement.x, placement.y, start_address,
                               memory_written))

    lines.append("txrx.write_memory({}, {}, {}, {})"
                 .format(placement.x, placement.y, user_o_register_address,
                         start_address))
    _append_to_rerun_script(binary_folder, lines)


def re_load_script_load_routing_tables(router_table, binary_folder, app_id):
    pickled_point = os.path.join(binary_folder,
                                 "picked_routing_table_for_{}_{}"
                                 .format(router_table.x, router_table.y))
    pickle.dump(router_table, open(pickled_point, 'wb'))
    lines = list()
    lines.append("router_table = pickle.load(open(\"{}\", ""\"rb\"))"
                 .format(ntpath.basename(pickled_point)))
    lines.append("txrx.load_multicast_routes(router_table.x, router_table.y, "
                 "router_table.multicast_routing_entries, app_id={})"
                 .format(app_id))
    _append_to_rerun_script(binary_folder, lines)


def re_load_script_load_executables_init(binary_folder, executable_targets):
    pickled_point = os.path.join(binary_folder, "picked_executables_mappings")
    pickle.dump(executable_targets, open(pickled_point, 'wb'))
    lines = list()
    lines.append("executable_targets = pickle.load(open(\"{}\", "
                 "\"rb\"))".format(ntpath.basename(pickled_point)))
    _append_to_rerun_script(binary_folder, lines)


def re_load_script_load_executables_individual(
        binary_folder, exectuable_target_key, app_id, size):
    lines = list()
    lines.append("core_subset = executable_targets[\"{}\"]"
                 .format(exectuable_target_key))
    lines.append("file_reader = SpinnmanFileDataReader(\"{}\")"
                 .format(exectuable_target_key))
    lines.append("txrx.execute_flood(core_subset, file_reader"
                 ", {}, {})".format(app_id, size))
    _append_to_rerun_script(binary_folder, lines)


def re_load_script_running_aspects(
        binary_folder, executable_targets, hostname, app_id, runtime):
    pickled_point = os.path.join(binary_folder, "picked_executable_targets")
    pickle.dump(executable_targets, open(pickled_point, 'wb'))
    lines = list()
    lines.append("executable_targets = pickle.load(open(\"{}\","" \"rb\"))"
                 .format(ntpath.basename(pickled_point)))
    lines.append("spinnaker_comms = SpynnakerCommsFunctions(None, None)")
    lines.append("spinnaker_comms._setup_interfaces(\"{}\")"
                 .format(hostname))
    lines.append("spinnaker_comms._start_execution_on_machine("
                 "executable_targets, {}, {})".format(app_id,
                                                      runtime))
    _append_to_rerun_script(binary_folder, lines)


def _write_router_diag(parent_xml_element, router_diagnostic_coords,
                       router_diagnostic):
    from lxml import etree
    router = \
        etree.SubElement(
            parent_xml_element, "router_at_chip_{}_{}"
                                .format(router_diagnostic_coords[0],
                                        router_diagnostic_coords[1]))
    etree.SubElement(router, "Loc__MC").text = \
        str(router_diagnostic.n_local_multicast_packets)
    etree.SubElement(router, "Ext__MC").text = \
        str(router_diagnostic.n_external_multicast_packets)
    etree.SubElement(router, "Dump_MC").text = \
        str(router_diagnostic.n_dropped_multicast_packets)
    etree.SubElement(router, "Loc__PP").text = \
        str(router_diagnostic.n_local_peer_to_peer_packets)
    etree.SubElement(router, "Ext__PP")\
        .text = str(router_diagnostic.n_external_peer_to_peer_packets)
    etree.SubElement(router, "Dump_PP")\
        .text = str(router_diagnostic.n_dropped_peer_to_peer_packets)
    etree.SubElement(router, "Loc__NN")\
        .text = str(router_diagnostic.n_local_nearest_neighbour_packets)
    etree.SubElement(router, "Ext__NN")\
        .text = str(router_diagnostic.n_external_nearest_neighbour_packets)
    etree.SubElement(router, "Dump_NN")\
        .text = str(router_diagnostic.n_dropped_nearest_neighbour_packets)
    etree.SubElement(router, "Loc__FR").text = \
        str(router_diagnostic.n_local_fixed_route_packets)
    etree.SubElement(router, "Ext__FR")\
        .text = str(router_diagnostic.n_external_fixed_route_packets)
    etree.SubElement(router, "Dump_FR")\
        .text = str(router_diagnostic.n_dropped_fixed_route_packets)


def generate_provance_routings(routing_tables, machine, txrx,
                               report_default_directory):
    #acquire diagnostic data
    router_diagnostics = dict()
    for router_table in routing_tables.routing_tables:
        router_diagnostic = txrx.\
            get_router_diagnostics(router_table.x, router_table.y)
        router_diagnostics[router_table.x, router_table.y] = \
            router_diagnostic
    from lxml import etree
    root = etree.Element("root")
    doc = etree.SubElement(root, "router_counters")
    expected_routers = etree.SubElement(doc, "Used_Routers")
    for router_diagnostic_coords in router_diagnostics.keys():
        _write_router_diag(
            expected_routers, router_diagnostic_coords,
            router_diagnostics[router_diagnostic_coords])
    unexpected_routers = etree.SubElement(doc, "Unexpected_Routers")
    for chip in machine.chips:
        coords = (chip.x, chip.y)
        if coords not in router_diagnostics.keys():
            router_diagnostic = \
                txrx.get_router_diagnostics(chip.x, chip.y)
            if (router_diagnostic.n_dropped_multicast_packets != 0 or
                    router_diagnostic.n_local_multicast_packets != 0 or
                    router_diagnostic.n_external_multicast_packets != 0):
                _write_router_diag(
                    unexpected_routers, router_diagnostic_coords,
                    router_diagnostics[router_diagnostic_coords])
    file_path = \
        os.path.join(report_default_directory, "provance_data.xml")
    writer = open(file_path, "w")
    writer.write(etree.tostring(root, pretty_print=True))
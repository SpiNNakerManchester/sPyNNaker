import logging
import os
import time

from spinnman import constants as spinnman_constants

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

    for key in processor_to_app_data_base_address:
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

        # params = vertex.parameters
        constraints = vertex.constraints
        f_network_specification.write(
            "AbstractConstrainedVertex {}, size: {}\n".format(label, size))
        f_network_specification.write("Model: {}\n".format(model))
        for constraint in constraints:
            constraint_str = constraint.label
            f_network_specification.write("constraint: {}\n"
                                          .format(constraint_str))
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
        edge_str = ("PartitionableEdge {} from vertex: '{}' ({} atoms)"
                    " to vertex: '{}' ({} atoms)\n".format(
                        label, pre_v_label, pre_v_sz, post_v_label, post_v_sz))
        f_network_specification.write(edge_str)
        f_network_specification.write("  Model: {}\n".format(model))
        f_network_specification.write("\n")
    # Close file:
    f_network_specification.close()


def _write_router_diag(parent_xml_element, chip_x, chip_y,
                       router_diagnostic, re_injected_counter):
    from lxml import etree
    router = etree.SubElement(
        parent_xml_element, "router_at_chip_{}_{}".format(chip_x, chip_y))
    etree.SubElement(router, "Loc__MC").text = str(
        router_diagnostic.n_local_multicast_packets)
    etree.SubElement(router, "Ext__MC").text = str(
        router_diagnostic.n_external_multicast_packets)
    etree.SubElement(router, "Dump_MC").text = str(
        router_diagnostic.n_dropped_multicast_packets)
    etree.SubElement(router, "Loc__PP").text = str(
        router_diagnostic.n_local_peer_to_peer_packets)
    etree.SubElement(router, "Ext__PP").text = str(
        router_diagnostic.n_external_peer_to_peer_packets)
    etree.SubElement(router, "Dump_PP").text = str(
        router_diagnostic.n_dropped_peer_to_peer_packets)
    etree.SubElement(router, "Loc__NN").text = str(
        router_diagnostic.n_local_nearest_neighbour_packets)
    etree.SubElement(router, "Ext__NN").text = str(
        router_diagnostic.n_external_nearest_neighbour_packets)
    etree.SubElement(router, "Dump_NN").text = str(
        router_diagnostic.n_dropped_nearest_neighbour_packets)
    etree.SubElement(router, "Loc__FR").text = str(
        router_diagnostic.n_local_fixed_route_packets)
    etree.SubElement(router, "Ext__FR").text = str(
        router_diagnostic.n_external_fixed_route_packets)
    etree.SubElement(router, "Dump_FR").text = str(
        router_diagnostic.n_dropped_fixed_route_packets)
    etree.SubElement(router, "Re__Inj").text = str(
        re_injected_counter)


def generate_provance_routings(routing_tables, machine, txrx,
                               report_default_directory):

    from lxml import etree
    root = etree.Element("root")
    doc = etree.SubElement(root, "router_counters")
    expected_routers = etree.SubElement(doc, "Used_Routers")
    unexpected_routers = etree.SubElement(doc, "Unexpected_Routers")

    # Get diagnostics from expected chips
    seen_chips = set()
    for router_table in routing_tables.routing_tables:
        if not machine.get_chip_at(router_table.x, router_table.y).virtual:
            if router_table.number_of_entries > 0:
                router_diagnostic = txrx.get_router_diagnostics(
                    router_table.x, router_table.y)
                re_inject_counter = _get_chips_re_injector_counter(
                    router_table.x, router_table.y, txrx)
                _write_router_diag(
                    expected_routers, router_table.x, router_table.y,
                    router_diagnostic, re_inject_counter)
                seen_chips.add((router_table.x, router_table.y))

    # Get diagnostics from unexpected chips
    for chip in machine.chips:
        if not chip.virtual:
            if (chip.x, chip.y) not in seen_chips:
                router_diagnostic = txrx.get_router_diagnostics(chip.x, chip.y)
                if (router_diagnostic.n_dropped_multicast_packets != 0 or
                        router_diagnostic.n_local_multicast_packets != 0 or
                        router_diagnostic.n_external_multicast_packets != 0):
                    re_inject_counter = _get_chips_re_injector_counter(
                        chip.x, chip.y, txrx)
                    _write_router_diag(
                        unexpected_routers, chip.x, chip.y, router_diagnostic,
                        re_inject_counter)

    # Write the details to a file
    file_path = os.path.join(report_default_directory, "provance_data.xml")
    writer = open(file_path, "w")
    writer.write(etree.tostring(root, pretty_print=True))


def _get_chips_re_injector_counter(chip_x, chip_y, txrx):
    """ helper method that checks for the re_injector core and reads its
    usr3 register

    :param chip_x: The x-coordinate of the chip to get the count from
    :param chip_y: The y-coordinate of the chip to get the count from
    :param txrx: the tranceiver object
    :return: a count of the re-injected packets
    """
    for processor in range(1, 17):
        data = txrx.get_cpu_information_from_core(chip_x, chip_y, processor)
        if data.application_id == spinnman_constants.RE_INJECTION_APP_ID:
            return data.user[0]

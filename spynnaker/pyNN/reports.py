import os
import time
import logging

logger = logging.getLogger(__name__)


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
        f_network_specification.write("Vertex {}, size: {}\n"
                                      .format(label, size))
        f_network_specification.write("Model: {}\n".format(model))
        if constraints.x is not None:
            if constraints.p is not None:
                constraint_str = "(x: {}, y: {}, p: {})"\
                    .format(constraints.x, constraints.y, constraints.p)
            else:
                constraint_str = "(x: {}, y: {})"\
                    .format(constraints.x, constraints.y)
            f_network_specification.write("  Placement constraint: {}\n"
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
        edge_str = "Edge {} from vertex: '{}' ({} atoms) to vertex: '{}' " \
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

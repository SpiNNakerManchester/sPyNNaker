from spynnaker.pyNN.exceptions import SpynnakerException

import os
import pickle


class ReloadScript(object):
    """ Generates a script for reloading a simulation
    """

    def __init__(self, binary_directory, hostname, board_version):
        self._binary_directory = binary_directory
        if not self._binary_directory.endswith(os.sep):
            self._binary_directory += os.sep
        file_name = self._binary_directory + "rerun_script.py"
        try:
            self._file = open(file_name, "w")
        except IOError:
            raise SpynnakerException("Cannot open {} to write the rerun script"
                                     .format(file_name))
        self._println("from spinn_machine.tags.iptag import IPTag")
        self._println("from spinn_machine.tags.reverse_iptag"
                      " import ReverseIPTag")
        self._println("")
        self._println("from spinnman.model.core_subsets import CoreSubsets")
        self._println("from spinnman.model.core_subset import CoreSubset")
        self._println("")
        self._println("from spynnaker.pyNN.utilities.reload.reload"
                      " import Reload")
        self._println("from spynnaker.pyNN.utilities.reload"
                      ".reload_application_data \\")
        self._println("    import ReloadApplicationData")
        self._println("from spynnaker.pyNN.utilities.reload.reload_binary"
                      " import ReloadBinary")
        self._println("from spynnaker.pyNN.utilities.reload"
                      ".reload_routing_table \\")
        self._println("    import ReloadRoutingTable")
        self._println("")
        self._println("machine_name = \"{}\"".format(hostname))
        self._println("machine_version = {}".format(board_version))
        self._println("")
        self._println("application_data = list()")
        self._println("routing_tables = list()")
        self._println("binaries = list()")
        self._println("iptags = list()")
        self._println("reverse_iptags = list()")
        self._println("")

    def _println(self, line):
        """ Write a line to the script

        :param line: The line to write
        :type line: str
        """
        self._file.write(line)
        self._file.write("\n")

    def add_application_data(self, application_data_file_name, placement,
                             base_address):
        relative_file_name = application_data_file_name.replace(
            self._binary_directory, "").replace("\\", "\\\\")
        self._println("application_data.append(ReloadApplicationData(")
        self._println("    \"{}\",".format(relative_file_name))
        self._println("    {}, {}, {}, {}))".format(placement.x, placement.y,
                                                    placement.p, base_address))

    def add_routing_table(self, routing_table):
        pickle_file_name = "picked_routing_table_for_{}_{}".format(
            routing_table.x, routing_table.y)
        pickle_file_path = self._binary_directory + pickle_file_name
        pickle_file = open(pickle_file_path, "wb")
        pickle.dump(routing_table, pickle_file)
        pickle_file.close()
        self._println("routing_tables.append(ReloadRoutingTable(")
        self._println("    \"{}\"))".format(pickle_file_name))

    def add_binary(self, binary_path, core_subsets):
        create_cs = "CoreSubsets(["
        for core_subset in core_subsets:
            create_cs += "CoreSubset({}, {}, ".format(core_subset.x,
                                                      core_subset.y)
            create_cs += "["
            for processor_id in core_subset.processor_ids:
                create_cs += "{}, ".format(processor_id)
            create_cs += "]),"
        create_cs += "])"
        self._println("binaries.append(ReloadBinary(")
        self._println("    \"{}\",".format(binary_path.replace("\\", "\\\\")))
        self._println("    {}))".format(create_cs))

    def add_ip_tag(self, iptag):
        self._println("iptags.append(IPTag(\"{}\", {}, \"{}\", {}, {}))"
                      .format(iptag.board_address, iptag.tag, iptag.ip_address,
                              iptag.port, iptag.strip_sdp))

    def add_reverse_ip_tag(self, reverse_ip_tag):
        self._println(
            "reverse_iptags.append(ReverseIPTag(\"{}\", {}, {}, {}, {}, {}))"
            .format(reverse_ip_tag.board_address, reverse_ip_tag.tag,
                    reverse_ip_tag.port, reverse_ip_tag.destination_x,
                    reverse_ip_tag.destination_y, reverse_ip_tag.destination_p,
                    reverse_ip_tag.sdp_port))

    def close(self):
        self._println("")
        self._println("reloader = Reload(machine_name, machine_version)")
        self._println("reloader.reload_application_data(application_data)")
        self._println("reloader.reload_routes(routing_tables)")
        self._println("reloader.reload_ip_tags(iptags)")
        self._println("reloader.reload_reverse_ip_tags(reverse_iptags)")
        self._println("reloader.reload_binaries(binaries)")
        self._println("reloader.restart()")
        self._file.close()

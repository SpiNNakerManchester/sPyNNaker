# Copyright (c) 2019-2020 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict
import logging
import os
import struct
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration)
from spinn_front_end_common.utilities import system_control_logic
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.utility_objs import ExecutableType

logger = logging.getLogger(__name__)


def _percent(a, b):
    if b == 0:
        return 0
    return 100.0 / b * a


class OnChipBitFieldGenerator(object):
    """ Executes bitfield and routing table entries for atom-based routing.
    """

    __slots__ = ("__placements", "__txrx")

    # flag which states that the binary finished cleanly.
    _SUCCESS = 0

    # the number of bytes needed to read the user2 register
    _USER_BYTES = 4

    # n key to n neurons maps size in words
    _N_KEYS_DATA_SET_IN_WORDS = 1

    # bits in a word
    _BITS_IN_A_WORD = 32

    # bit to mask a bit
    _BIT_MASK = 1

    # n region data sets size in words
    _N_REGION_DATA_SETS_IN_WORDS = 1

    # n elements in each key to n atoms map
    _N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP = 2

    _BYTES_PER_FILTER = 12

    _ONE_WORDS = struct.Struct("<I")

    # bit field report file name
    _BIT_FIELD_REPORT_FILENAME = "generated_bit_fields.rpt"
    _BIT_FIELD_SUMMARY_REPORT_FILENAME = "bit_field_summary.rpt"

    # binary name
    _BIT_FIELD_EXPANDER_APLX = "bit_field_expander.aplx"

    def __call__(
            self, placements, app_graph, executable_finder,
            provenance_file_path, transceiver, graph_mapper,
            read_bit_field_generator_iobuf, generating_bitfield_report,
            default_report_folder, machine_graph, routing_infos,
            generating_bit_field_summary_report):
        """ loads and runs the bit field generator on chip

        :param ~.Placements placements: placements
        :param ~.ApplicationGraph app_graph: the app graph
        :param ~.ExecutableFinder executable_finder: the executable finder
        :param str provenance_file_path:
            the path to where provenance data items is written
        :param ~.Transceiver transceiver: the SpiNNMan instance
        :param graph_mapper: mapper between application an machine graphs.
        :param bool read_bit_field_generator_iobuf: flag for report
        :param bool generating_bitfield_report: flag for report
        :param str default_report_folder: the file path for reports
        :param ~.MachineGraph machine_graph: the machine graph
        :param ~.RoutingInfo routing_infos: the key to edge map
        :param bool generating_bit_field_summary_report:
            flag for making summary report
        """
        self.__placements = placements
        self.__txrx = transceiver

        # progress bar
        progress = ProgressBar(
            len(app_graph.vertices) + 2,
            "Running bitfield generation on chip")

        # get data
        expander_cores = self._calculate_core_data(
            app_graph, graph_mapper, progress, executable_finder)

        # load data
        bit_field_app_id = transceiver.app_id_tracker.get_new_id()
        progress.update()

        # run app
        system_control_logic.run_system_application(
            expander_cores, bit_field_app_id, transceiver,
            provenance_file_path, executable_finder,
            read_bit_field_generator_iobuf, self.__check_for_success,
            None, [CPUState.FINISHED], False, 0,
            "bit_field_expander_on_{}_{}_{}.txt")
        # update progress bar
        progress.end()

        # read in bit fields for debugging purposes
        if generating_bitfield_report:
            self._full_report_bit_fields(
                app_graph, graph_mapper, default_report_folder,
                self._BIT_FIELD_REPORT_FILENAME)
        if generating_bit_field_summary_report:
            self._summarise_bit_fields(
                app_graph, graph_mapper, default_report_folder,
                self._BIT_FIELD_SUMMARY_REPORT_FILENAME)

    def _summarise_bit_fields(
            self, app_graph, graph_mapper,
            default_report_folder, bit_field_summary_report_name):
        """ summary report of the bitfields that were generated

        :param ~.ApplicationGraph app_graph: app graph
        :param graph_mapper: the graph mapper
        :param str default_report_folder: the file path for where reports are
        :param str bit_field_summary_report_name: the name of the summary file
        """
        progress = ProgressBar(
            app_graph.n_vertices,
            "reading back bitfields from chip for summary report")

        chip_packet_count = defaultdict(int)
        chip_redundant_count = defaultdict(int)

        file_path = os.path.join(
            default_report_folder, bit_field_summary_report_name)
        output = open(file_path, "w")

        # read in for each app vertex that would have a bitfield
        for app_vertex in progress.over(app_graph.vertices):
            for vertex in graph_mapper.get_machine_vertices(app_vertex):
                if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                    self.__summarise_vertex_bitfields(
                        vertex, chip_packet_count, chip_redundant_count,
                        output)

        output.write("\n\n\n")

        # overall summary
        total_packets = 0
        total_redundant_packets = 0
        for xy in chip_packet_count:
            x, y = xy
            output.write(
                "chip {}:{} has a total incoming packet count of {} and a "
                "redundant packet count of {} given a redundant "
                "percentage of {} \n".format(
                    x, y, chip_packet_count[xy], chip_redundant_count[xy],
                    _percent(chip_redundant_count[xy], chip_packet_count[xy])))

            total_packets += chip_packet_count[xy]
            total_redundant_packets += chip_redundant_count[xy]

        percentage = _percent(total_redundant_packets, total_packets)

        output.write(
            "overall the application has estimated {} packets flying around "
            "of which {} are redundant at reception. this is a {} percentage "
            "of the packets".format(
                total_packets, total_redundant_packets, percentage))
        output.close()

    def __summarise_vertex_bitfields(
            self, vertex, chip_count, redundant_count, f):
        """
        :param AbstractSupportsBitFieldGeneration vertex:
        :param dict(tuple(int,int),int) chip_count:
        :param dict(tuple(int,int),int) redundant_count:
        :param ~io.TextIOBase f:
        """
        local_total = 0
        local_redundant = 0
        placement = self.__placements.get_placement_of_vertex(vertex)

        # read in each bitfield
        for _master_pop_key, bit_field in self.__bitfields(vertex):
            for neuron_id in range(0, len(bit_field) * self._BITS_IN_A_WORD):
                if self._bit_for_neuron_id(bit_field, neuron_id) == 0:
                    redundant_count[placement.x, placement.y] += 1
                    local_redundant += 1
                chip_count[placement.x, placement.y] += 1
                local_total += 1

        redundant_packet_percentage = _percent(local_redundant, local_total)

        f.write(
            "vertex on {}:{}:{} has total incoming packet count of {} and a "
            "redundant packet count of {}, making a redundancy rate of {}%"
            "\n".format(
                placement.x, placement.y, placement.p,
                local_total, local_redundant, redundant_packet_percentage))

    def _full_report_bit_fields(
            self, app_graph, graph_mapper,
            default_report_folder, bit_field_report_name):
        """ report of the bitfields that were generated

        :param ~.ApplicationGraph app_graph: app graph
        :param graph_mapper: the graph mapper
        :param str default_report_folder: the file path for where reports are.
        :param str bit_field_report_name: the name of the file
        """

        # generate file
        progress = ProgressBar(
            app_graph.n_vertices, "reading back bitfields from chip")

        file_path = os.path.join(default_report_folder, bit_field_report_name)
        with open(file_path, "w") as output:
            # read in for each app vertex that would have a bitfield
            for app_vertex in progress.over(app_graph.vertices):
                for vertex in graph_mapper.get_machine_vertices(app_vertex):
                    if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                        self.__report_vertex_bitfields(vertex, output)

    def __report_vertex_bitfields(self, vertex, f):
        """
        :param AbstractSupportsBitFieldGeneration vertex:
        :param ~io.TextIOBase f:
        """
        placement = self.__placements.get_placement_of_vertex(vertex)
        f.write("For core {}:{}:{}. Bitfields as follows:\n\n".format(
            placement.x, placement.y, placement.p))

        # read in each bitfield
        for master_pop_key, bit_field in self.__bitfields(vertex):
            # put into report
            n_neurons = len(bit_field) * self._BITS_IN_A_WORD
            for neuron_id in range(0, n_neurons):
                f.write("for key {} neuron id {} has bit {} set\n".format(
                    master_pop_key, neuron_id,
                    self._bit_for_neuron_id(bit_field, neuron_id)))

    def __bitfields(self, vertex):
        """ Reads the bitfields of a machine vertex off the machine.

        :param AbstractSupportsBitFieldGeneration vertex:
        :return: sequence of bitfield records, one per bitfield.
            Each contains a bitfield's `master_pop_key`, `bitfield_data`
        :rtype: iterable(tuple(int,list(int)))
        """
        # get bitfield address
        placement = self.__placements.get_placement_of_vertex(vertex)
        address = vertex.bit_field_base_address(self.__txrx, placement)

        # read how many bitfields there are
        n_bit_fields, = struct.unpack("<I", self.__txrx.read_memory(
            placement.x, placement.y, address, BYTES_PER_WORD))
        address += BYTES_PER_WORD

        # read in each bitfield
        for _index in range(0, n_bit_fields):
            master_pop_key, size, addr = struct.unpack(
                "<III", self.__txrx.read_memory(
                    placement.x, placement.y, address, self._BYTES_PER_FILTER))
            address += self._BYTES_PER_FILTER
            data = struct.unpack(
                "<{}I".format(size), self.__txrx.read_memory(
                    placement.x, placement.y, addr, size * BYTES_PER_WORD))
            yield master_pop_key, data

    def _bit_for_neuron_id(self, bitfield_data, neuron_id):
        """ locate the bit for the neuron in the bitfield

        :param list(int) bitfield_data:
            the block of words which represent the bitfield
        :param int neuron_id: the neuron id to find the bit in the bitfield
        :return: the bit
        :rtype: int
        """
        word_id, bit_in_word = divmod(neuron_id, self._BITS_IN_A_WORD)
        flag = (bitfield_data[word_id] >> bit_in_word) & self._BIT_MASK
        return flag

    def _calculate_core_data(
            self, app_graph, graph_mapper, progress, executable_finder):
        """ gets the data needed for the bit field expander for the machine

        :param ~.ApplicationGraph app_graph: app graph
        :param graph_mapper: graph mapper between app graph and machine graph
        :param ~.ProgressBar progress: progress bar
        :param ~.ExecutableFinder executable_finder:
            where to find the executable
        :return: expander cores
        :rtype: ~.ExecutableTargets
        """

        # cores to place bitfield expander
        expander_cores = ExecutableTargets()

        # bit field expander executable file path
        binary_path = executable_finder.get_executable_path(
            self._BIT_FIELD_EXPANDER_APLX)

        # locate verts which can have a synaptic matrix to begin with
        for app_vertex in progress.over(app_graph.vertices, False):
            machine_verts = graph_mapper.get_machine_vertices(app_vertex)
            for vertex in machine_verts:
                if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                    self.__set_bitfield_builder_region(
                        vertex, expander_cores, binary_path)
        return expander_cores

    def __set_bitfield_builder_region(
            self, vertex, targets, binary_path):
        """ helper for :py:meth:`_calculate_core_data`

        :param AbstractSupportsBitFieldGeneration vertex:
        :param ~.ExecutableTargets targets:
        :param str binary_path:
        """
        placement = self.__placements.get_placement_of_vertex(vertex)

        # check if the chip being considered already.
        targets.add_processor(
            binary_path, placement.x, placement.y, placement.p,
            executable_type=ExecutableType.SYSTEM)

        region_address = vertex.bit_field_builder_region(
            self.__txrx, placement)

        # update user 1 with location
        self.__txrx.write_memory(
            placement.x, placement.y,
            self.__txrx.get_user_1_register_address_from_core(placement.p),
            self._ONE_WORDS.pack(region_address), self._USER_BYTES)

    def __check_for_success(self, executable_targets, transceiver):
        """ Goes through the cores checking for cores that have failed to\
            expand the bitfield to the core

        :param ~.ExecutableTargets executable_targets:
            cores to load bitfield on
        :param ~.Transceiver transceiver: SpiNNMan instance
        :rtype: bool
        """
        for core_subset in executable_targets.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:
                # Read the result from USER0 register
                user_2_base_address = \
                    transceiver.get_user_2_register_address_from_core(p)
                result, = struct.unpack("<I", transceiver.read_memory(
                    x, y, user_2_base_address, self._USER_BYTES))

                # The result is 0 if success, otherwise failure
                if result != self._SUCCESS:
                    return False
        return True

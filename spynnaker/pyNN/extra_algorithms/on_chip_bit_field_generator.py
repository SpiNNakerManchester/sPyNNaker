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
import math
import os
import struct
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration)
from spinn_front_end_common.utilities.system_control_logic import (
    run_system_application)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.utility_objs import ExecutableType

logger = logging.getLogger(__name__)
_ONE_WORD = struct.Struct("<I")
_THREE_WORDS = struct.Struct("<III")


def _percent(amount, total):
    if total == 0:
        return 0.0
    return (100.0 * amount) / float(total)


class OnChipBitFieldGenerator(object):
    """ Executes bitfield and routing table entries for atom based routing

    :param ~pacman.model.placementsPlacements placements: placements
    :param ~pacman.model.graphs.application.ApplicationGraph app_graph:
        the app graph
    :param executable_finder: the executable finder
    :type executable_finder:
        ~spinn_front_end_common.utilities.utility_objs.ExecutableFinder
    :param str provenance_file_path:
        the path to where provenance data items is written
    :param ~spinnman.transceiver.Transceiver transceiver:
        the SpiNNMan instance
    :param bool read_bit_field_generator_iobuf: flag for report
    :param bool generating_bitfield_report: flag for report
    :param str default_report_folder: the file path for reports
    :param ~pacman.model.graphs.machine.MachineGraph machine_graph:
        the machine graph
    :param ~pacman.model.routing_info.RoutingInfo routing_infos:
        the key to edge map
    :param bool generating_bit_field_summary_report:
        flag for making summary report
    """

    __slots__ = ("__transceiver", "__placements")

    # flag which states that the binary finished cleanly.
    _SUCCESS = 0

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

    # bit field report file name
    _BIT_FIELD_REPORT_FILENAME = "generated_bit_fields.rpt"
    _BIT_FIELD_SUMMARY_REPORT_FILENAME = "bit_field_summary.rpt"

    # binary name
    _BIT_FIELD_EXPANDER_APLX = "bit_field_expander.aplx"

    def __call__(
            self, placements, app_graph, executable_finder,
            provenance_file_path, transceiver,
            read_bit_field_generator_iobuf, generating_bitfield_report,
            default_report_folder, machine_graph, routing_infos,
            generating_bit_field_summary_report):
        """ loads and runs the bit field generator on chip

        :param ~.Placements placements:
        :param ~.ApplicationGraph app_graph:
        :param executable_finder:
        :type executable_finder:
            ~spinn_front_end_common.utilities.utility_objs.ExecutableFinder
        :param str provenance_file_path:
        :param ~.Transceiver transceiver:
        :param bool read_bit_field_generator_iobuf:
        :param bool generating_bitfield_report:
        :param str default_report_folder:
        :param ~.MachineGraph machine_graph:
        :param ~.RoutingInfo routing_infos: the key to edge map
        :param bool generating_bit_field_summary_report:
        """
        self.__transceiver = transceiver
        self.__placements = placements

        # progress bar
        progress = ProgressBar(
            len(app_graph.vertices) * 2 + 1,
            "Running bitfield generation on chip")

        # get data
        expander_cores = self._calculate_core_data(
            app_graph, progress, executable_finder.get_executable_path(
                self._BIT_FIELD_EXPANDER_APLX))

        # load data
        bit_field_app_id = transceiver.app_id_tracker.get_new_id()
        progress.update(1)

        # run app
        run_system_application(
            expander_cores, bit_field_app_id, transceiver,
            provenance_file_path, executable_finder,
            read_bit_field_generator_iobuf, _check_for_success,
            [CPUState.FINISHED], False,
            "bit_field_expander_on_{}_{}_{}.txt", progress_bar=progress)
        # update progress bar
        progress.end()

        # read in bit fields for debugging purposes
        if generating_bitfield_report:
            self._read_back_bit_fields(app_graph, default_report_folder)
        if generating_bit_field_summary_report:
            self._read_back_and_summarise_bit_fields(
                app_graph, default_report_folder)

    def _read_back_and_summarise_bit_fields(
            self, app_graph, default_report_folder):
        """ summary report of the bitfields that were generated

        :param ~.ApplicationGraph app_graph: app graph
        :param str default_report_folder: the file path for where reports are
        """
        progress = ProgressBar(
            len(app_graph.vertices),
            "reading back bitfields from chip for summary report")

        chip_packet_count = defaultdict(int)
        chip_redundant_count = defaultdict(int)

        file_path = os.path.join(
            default_report_folder, self._BIT_FIELD_SUMMARY_REPORT_FILENAME)
        with open(file_path, "w") as output:
            # read in for each app vertex that would have a bitfield
            for app_vertex in progress.over(app_graph.vertices):
                # get machine verts
                for placement in self.__bitfield_placements(app_vertex):
                    local_total = 0
                    local_redundant = 0

                    xy = (placement.x, placement.y)
                    for _, n_neurons, bit_field in self.__bitfields(placement):
                        for neuron_id in range(n_neurons):
                            if (self._bit_for_neuron_id(
                                    bit_field, neuron_id) == 0):
                                chip_redundant_count[xy] += 1
                                local_redundant += 1
                            chip_packet_count[xy] += 1
                            local_total += 1

                    redundant_packet_percentage = _percent(
                        local_redundant, local_total)

                    output.write(
                        "vertex on {}:{}:{} has total incoming packet "
                        "count of {} and a redundant packet count of {}. "
                        "Making a redundancy ratio of {}%\n".format(
                            placement.x, placement.y, placement.p,
                            local_total, local_redundant,
                            redundant_packet_percentage))

            output.write("\n\n\n")

            # overall summary
            total_packets = 0
            total_redundant_packets = 0
            for xy in chip_packet_count:
                x, y = xy
                output.write(
                    "chip {}:{} has a total incoming packet count of {} and "
                    "a redundant packet count of {} given a redundancy ratio "
                    "of {}%\n".format(
                        x, y, chip_packet_count[xy],
                        chip_redundant_count[xy],
                        _percent(chip_redundant_count[xy],
                                 chip_packet_count[xy])))

                total_packets += chip_packet_count[xy]
                total_redundant_packets += chip_redundant_count[xy]

            percentage = _percent(total_redundant_packets, total_packets)

            output.write(
                "overall the application has estimated {} packets flying "
                "around of which {} are redundant at reception. This is "
                "{}% of the packets".format(
                    total_packets, total_redundant_packets, percentage))

    def __bitfield_placements(self, app_vertex):
        """ The placements of the machine vertices of the given app vertex \
            that support the AbstractSupportsBitFieldGeneration protocol.

        :param ~.ApplicationVertex app_vertex:
        :rtype: iterable(~.Placement)
        """
        for vertex in app_vertex.machine_vertices:
            if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                yield self.__placements.get_placement_of_vertex(vertex)

    def __bitfields(self, placement):
        """ Reads back the bitfields that have been placed on a vertex.

        :param ~.Placement placement:
            The vertex must support AbstractSupportsBitFieldGeneration
        :returns: list of (master population key, num bits, bitfield data)
        :rtype: iterable(tuple(int,int,list(int)))
        """
        # get bitfield address
        address = placement.vertex.bit_field_base_address(
            self.__transceiver, placement)

        # read how many bitfields there are
        n_bit_field_entries, = _ONE_WORD.unpack(
            self.__transceiver.read_memory(
                placement.x, placement.y, address, _ONE_WORD.size))
        address += _ONE_WORD.size

        # read in each bitfield
        for _bit_field_index in range(n_bit_field_entries):
            # master pop key, n words and read pointer
            master_pop_key, n_words, read_pointer = \
                _THREE_WORDS.unpack(self.__transceiver.read_memory(
                    placement.x, placement.y, address, _THREE_WORDS.size))
            address += _THREE_WORDS.size

            # get bitfield words
            bit_field = struct.unpack(
                "<{}I".format(n_words),
                self.__transceiver.read_memory(
                    placement.x, placement.y, read_pointer,
                    n_words * BYTES_PER_WORD))
            yield master_pop_key, n_words * self._BITS_IN_A_WORD, bit_field

    def _read_back_bit_fields(
            self, app_graph, default_report_folder):
        """ report of the bitfields that were generated

        :param ~.ApplicationGraph app_graph: app graph
        :param str default_report_folder: the file path for where reports are
        """

        # generate file
        progress = ProgressBar(
            len(app_graph.vertices), "reading back bitfields from chip")

        file_path = os.path.join(
            default_report_folder, self._BIT_FIELD_REPORT_FILENAME)
        with open(file_path, "w") as output:
            # read in for each app vertex that would have a bitfield
            for app_vertex in progress.over(app_graph.vertices):
                # get machine verts
                for placement in self.__bitfield_placements(app_vertex):
                    self.__read_back_single_core_data(placement, output)

    def __read_back_single_core_data(self, placement, f):
        """
        :param ~.Placement placement:
        :param ~io.TextIOBase f:
        """
        f.write("For core {}:{}:{}. Bitfields as follows:\n\n".format(
            placement.x, placement.y, placement.p))

        for master_pop_key, n_bits, bit_field in self.__bitfields(placement):
            # put into report
            for neuron_id in range(n_bits):
                f.write("for key {}, neuron id {} has bit {} set\n".format(
                    master_pop_key, neuron_id,
                    self._bit_for_neuron_id(bit_field, neuron_id)))

    @classmethod
    def _bit_for_neuron_id(cls, bit_field, neuron_id):
        """ locate the bit for the neuron in the bitfield

        :param list(int) bit_field:
            the block of words which represent the bitfield
        :param int neuron_id: the neuron id to find the bit in the bitfield
        :return: the bit
        :rtype: int
        """
        word_id = int(math.floor(neuron_id // cls._BITS_IN_A_WORD))
        bit_in_word = neuron_id % cls._BITS_IN_A_WORD
        flag = (bit_field[word_id] >> bit_in_word) & cls._BIT_MASK
        return flag

    def _calculate_core_data(
            self, app_graph, progress, bit_field_expander_path):
        """ gets the data needed for the bit field expander for the machine

        :param ~.ApplicationGraph app_graph: app graph
        :param ~.ProgressBar progress: progress bar
        :param str bit_field_expander_path: where to find the executable
        :return: data and expander cores
        :rtype: ExecutableTargets
        """
        # cores to place bitfield expander
        expander_cores = ExecutableTargets()

        # locate verts which can have a synaptic matrix to begin with
        for app_vertex in progress.over(app_graph.vertices, False):
            for placement in self.__bitfield_placements(app_vertex):
                self.__write_single_core_data(
                    placement, bit_field_expander_path, expander_cores)

        return expander_cores

    def __write_single_core_data(
            self, placement, bit_field_expander_path, expander_cores):
        """
        :param ~.Placement placement:
            The vertex must support AbstractSupportsBitFieldGeneration
        :param str bit_field_expander_path:
        :param ~.ExecutableTargets expander_cores:
        """
        # check if the chip being considered already.
        expander_cores.add_processor(
            bit_field_expander_path, placement.x, placement.y,
            placement.p, executable_type=ExecutableType.SYSTEM)

        bit_field_builder_region = placement.vertex.bit_field_builder_region(
            self.__transceiver, placement)
        # update user 1 with location
        user_1_base_address = \
            self.__transceiver.get_user_1_register_address_from_core(
                placement.p)
        self.__transceiver.write_memory(
            placement.x, placement.y, user_1_base_address,
            _ONE_WORD.pack(bit_field_builder_region), _ONE_WORD.size)


def _check_for_success(executable_targets, transceiver):
    """ Goes through the cores checking for cores that have failed to\
        expand the bitfield to the core

    :param ~.ExecutableTargets executable_targets:
        cores to load bitfield on
    :param ~.Transceiver transceiver: SpiNNMan instance
    """
    for core_subset in executable_targets.all_core_subsets:
        x = core_subset.x
        y = core_subset.y
        for p in core_subset.processor_ids:
            # Read the result from USER0 register
            user_2_base_address = \
                transceiver.get_user_2_register_address_from_core(p)
            result, = _ONE_WORD.unpack(transceiver.read_memory(
                x, y, user_2_base_address, _ONE_WORD.size))

            # The result is 0 if success, otherwise failure
            if result != OnChipBitFieldGenerator._SUCCESS:
                return False
    return True

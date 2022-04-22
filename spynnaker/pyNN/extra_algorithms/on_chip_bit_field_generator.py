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
import os
import struct
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spinn_front_end_common.abstract_models import (
    AbstractSupportsBitFieldGeneration)
from spinn_front_end_common.utilities import system_control_logic
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spinn_front_end_common.utilities.helpful_functions import n_word_struct
from spynnaker.pyNN.data import SpynnakerDataView

_THREE_WORDS = struct.Struct("<III")
# bits in a word
_BITS_IN_A_WORD = 32
# bit to mask a bit
_BIT_MASK = 1


def _bit_for_neuron_id(bitfield, neuron_id):
    """ Get the bit for a neuron in the bitfield.

    :param list(int) bitfield:
        the block of words which represent the bitfield
    :param int neuron_id: the neuron id to find the bit in the bitfield
    :return: the bit (``0`` or ``1``)
    :rtype: int
    """
    word_id, bit_in_word = divmod(neuron_id, _BITS_IN_A_WORD)
    return (bitfield[word_id] >> bit_in_word) & _BIT_MASK


def _percent(amount, total):
    if total == 0:
        return 0.0
    return (100.0 * amount) / float(total)


def on_chip_bitfield_generator():
    """ Loads and runs the bit field generator on chip.

    """
    generator = _OnChipBitFieldGenerator()
    generator._run()


class _OnChipBitFieldGenerator(object):
    """ Executes bitfield and routing table entries for atom based routing.
    """

    __slots__ = ("__aplx", "__txrx")

    # flag which states that the binary finished cleanly.
    _SUCCESS = 0

    # bit field report file names
    _BIT_FIELD_REPORT_FILENAME = "generated_bit_fields.rpt"
    _BIT_FIELD_SUMMARY_REPORT_FILENAME = "bit_field_summary.rpt"

    # Bottom 30 bits
    _N_WORDS_MASK = 0x3FFFFFFF

    # binary name
    _BIT_FIELD_EXPANDER_APLX = "bit_field_expander.aplx"

    # Messages used to build the summary report
    _PER_CORE_SUMMARY = (
        "Vertex on {}:{}:{} ({}) has total incoming packet count of {} and "
        "a redundant packet count of {}, making a redundant packet rate of "
        "{}%\n")
    _PER_CHIP_SUMMARY = (
        "Chip {}:{} has a total incoming packet count of {} and a redundant "
        "packet count of {} given a redundancy rate of {}%\n")
    _OVERALL_SUMMARY = (
        "Overall, the application has estimated {} packets flying around of "
        "which {} are redundant at reception. This is {}% of the packets\n")

    # Messages used to build the detailed report
    _CORE_DETAIL = "For core {}:{}:{} ({}), bitfields as follows:\n\n"
    _FIELD_DETAIL = "    For key {}, neuron id {} has bit == {}\n"

    def __init__(self):
        """ Loads and runs the bit field generator on chip.

        """
        self.__txrx = None
        self.__aplx = SpynnakerDataView.get_executable_path(
            self._BIT_FIELD_EXPANDER_APLX)

    def _run(self):
        """ Loads and runs the bit field generator on chip.

        :param ~spinnman.transceiver.Transceiver transceiver:
            the SpiNNMan instance
        """
        self.__txrx = SpynnakerDataView.get_transceiver()
        app_graph = SpynnakerDataView.get_runtime_graph()
        machine_graph = SpynnakerDataView.get_runtime_machine_graph()
        # progress bar
        progress = ProgressBar(
            app_graph.n_vertices + machine_graph.n_vertices + 1,
            "Running bitfield generation on chip")

        # get data
        expander_cores = self._calculate_core_data(app_graph, progress)

        # load data
        bit_field_app_id = SpynnakerDataView.get_new_id()
        progress.update(1)

        # run app
        system_control_logic.run_system_application(
            expander_cores, bit_field_app_id,
            get_config_bool("Reports", "write_bit_field_iobuf"),
            self.__check_for_success, [CPUState.FINISHED], False,
            "bit_field_expander_on_{}_{}_{}.txt", progress_bar=progress)
        # update progress bar
        progress.end()

        # read in bit fields for debugging purposes
        run_dir_path = SpynnakerDataView.get_run_dir_path()
        if get_config_bool("Reports", "generate_bit_field_report"):
            self._full_report_bit_fields(app_graph, os.path.join(
                run_dir_path, self._BIT_FIELD_REPORT_FILENAME))
            self._summary_report_bit_fields(app_graph, os.path.join(
                run_dir_path, self._BIT_FIELD_SUMMARY_REPORT_FILENAME))

    def _summary_report_bit_fields(self, app_graph, file_path):
        """ summary report of the bitfields that were generated

        :param ~.ApplicationGraph app_graph: app graph
        :param str file_path: Where to write to
        """
        chip_packet_count = defaultdict(int)
        chip_redundant_count = defaultdict(int)
        progress = ProgressBar(
            app_graph.n_vertices,
            "reading back bitfields from chip for summary report")
        with open(file_path, "w") as output:
            # read in for each app vertex that would have a bitfield
            for app_vertex in progress.over(app_graph.vertices):
                # get machine verts
                for placement in self.__bitfield_placements(app_vertex):
                    local_total = 0
                    local_redundant = 0
                    xy = (placement.x, placement.y)
                    for _, n_neurons, bitfield in self.__bitfields(placement):
                        for neuron_id in range(n_neurons):
                            if not _bit_for_neuron_id(bitfield, neuron_id):
                                chip_redundant_count[xy] += 1
                                local_redundant += 1
                        local_total += n_neurons
                    chip_packet_count[xy] = local_total
                    output.write(self._PER_CORE_SUMMARY.format(
                        placement.x, placement.y, placement.p,
                        placement.vertex.label,
                        local_total, local_redundant,
                        _percent(local_redundant, local_total)))

            output.write("\n\n\n")

            # overall summary
            total_packets = 0
            total_redundant_packets = 0
            for xy in chip_packet_count:
                x, y = xy
                output.write(self._PER_CHIP_SUMMARY.format(
                    x, y, chip_packet_count[xy], chip_redundant_count[xy],
                    _percent(chip_redundant_count[xy], chip_packet_count[xy])))
                total_packets += chip_packet_count[xy]
                total_redundant_packets += chip_redundant_count[xy]

            output.write(self._OVERALL_SUMMARY.format(
                total_packets, total_redundant_packets,
                _percent(total_redundant_packets, total_packets)))

    def _full_report_bit_fields(self, app_graph, file_path):
        """ report of the bitfields that were generated

        :param ~.ApplicationGraph app_graph: app graph
        :param str file_path: Where to write to
        """
        progress = ProgressBar(
            app_graph.n_vertices, "reading back bitfields from chip")
        with open(file_path, "w") as output:
            # read in for each app vertex that would have a bitfield
            for app_vertex in progress.over(app_graph.vertices):
                # get machine verts
                for placement in self.__bitfield_placements(app_vertex):
                    self.__read_back_single_core_data(placement, output)

    def __read_back_single_core_data(self, placement, f):
        """
        :param ~.Placement placement:
        :param f:
        """
        f.write(self._CORE_DETAIL.format(
            placement.x, placement.y, placement.p, placement.vertex.label))

        for master_pop_key, n_bits, bitfield in self.__bitfields(placement):
            # put into report
            for neuron_id in range(n_bits):
                f.write(self._FIELD_DETAIL.format(
                    master_pop_key, neuron_id,
                    _bit_for_neuron_id(bitfield, neuron_id)))

    def __bitfield_placements(self, app_vertex):
        """ The placements of the machine vertices of the given app vertex \
            that support the AbstractSupportsBitFieldGeneration protocol.

        :param ~.ApplicationVertex app_vertex:
        :rtype: iterable(~.Placement)
        """
        for vertex in app_vertex.machine_vertices:
            if isinstance(vertex, AbstractSupportsBitFieldGeneration):
                yield SpynnakerDataView.get_placement_of_vertex(vertex)

    def __bitfields(self, placement):
        """ Reads back the bitfields that have been placed on a vertex.

        :param ~.Placement placement:
            The vertex must support AbstractSupportsBitFieldGeneration
        :returns: sequence of (master population key, num bits, bitfield data)
        :rtype: iterable(tuple(int,int,list(int)))
        """
        # get bitfield address
        address = placement.vertex.bit_field_base_address(placement)

        # read how many bitfields there are; header of filter_region_t
        _merged, _redundant, total = _THREE_WORDS.unpack(
            self.__txrx.read_memory(
                placement.x, placement.y, address, _THREE_WORDS.size))
        address += _THREE_WORDS.size

        # read in each bitfield
        for _bit_field_index in range(total):
            # master pop key, n words and read pointer; filter_info_t
            master_pop_key, n_words, read_pointer = _THREE_WORDS.unpack(
                self.__txrx.read_memory(
                    placement.x, placement.y, address, _THREE_WORDS.size))
            address += _THREE_WORDS.size
            # Mask off merged and all_ones flag bits
            n_words &= self._N_WORDS_MASK

            # get bitfield words
            if n_words:
                bitfield = n_word_struct(n_words).unpack(
                    self.__txrx.read_memory(
                        placement.x, placement.y, read_pointer,
                        n_words * BYTES_PER_WORD))
            else:
                bitfield = []
            yield master_pop_key, n_words * _BITS_IN_A_WORD, bitfield

    def _calculate_core_data(self, app_graph, progress):
        """ gets the data needed for the bit field expander for the machine

        :param ~.ApplicationGraph app_graph: app graph
        :param ~.ProgressBar progress: progress bar
        :return: data and expander cores
        :rtype: ~.ExecutableTargets
        """
        # cores to place bitfield expander
        expander_cores = ExecutableTargets()

        # bit field expander executable file path
        # locate verts which can have a synaptic matrix to begin with
        for app_vertex in progress.over(app_graph.vertices, False):
            for placement in self.__bitfield_placements(app_vertex):
                self.__write_single_core_data(placement, expander_cores)

        return expander_cores

    def __write_single_core_data(self, placement, expander_cores):
        """
        :param ~.Placement placement:
        :param ~.ExecutableTargets expander_cores:
        """
        # check if the chip being considered already.
        expander_cores.add_processor(
            self.__aplx, placement.x, placement.y, placement.p,
            executable_type=ExecutableType.SYSTEM)

        bit_field_builder_region = placement.vertex.bit_field_builder_region(
            self.__txrx, placement)
        # update user 1 with location
        user_1_base_address = \
            self.__txrx.get_user_1_register_address_from_core(placement.p)
        self.__txrx.write_memory(
            placement.x, placement.y, user_1_base_address,
            bit_field_builder_region)

    def __check_for_success(self, executable_targets):
        """ Goes through the cores checking for cores that have failed to\
            expand the bitfield to the core

        :param ~.ExecutableTargets executable_targets:
            cores to load bitfield on
        :param ~.Transceiver transceiver: SpiNNMan instance
        :rtype: bool
        """
        transceiver = SpynnakerDataView.get_transceiver()
        for core_subset in executable_targets.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:
                # Read the result from USER0 register
                result = transceiver.read_word(
                    x, y, transceiver.get_user_2_register_address_from_core(p))

                # The result is 0 if success, otherwise failure
                if result != self._SUCCESS:
                    return False
        return True

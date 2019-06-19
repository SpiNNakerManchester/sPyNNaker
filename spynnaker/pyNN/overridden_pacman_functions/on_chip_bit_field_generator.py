import functools
import math
from collections import defaultdict

from spinn_front_end_common.interface.interface_functions import \
    ChipIOBufExtractor
from spinn_front_end_common.utilities.exceptions import SpinnFrontEndException
from spinn_front_end_common.utilities import system_control_logic
from spinn_front_end_common.utilities.constants import WORD_TO_BYTE_MULTIPLIER

from spinn_utilities.progress_bar import ProgressBar

from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState

import struct
import logging
import os

from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
logger = logging.getLogger(__name__)


class OnChipBitFieldGenerator(object):
    """ Executes bitfield and routing table entries for atom based routing
    """

    __slots__ = ()

    # flag which states that the binary finished cleanly.
    _SUCCESS = 0

    # the number of bytes needed to read the user2 register
    _USER_2_BYTES = 4

    # n key to n neurons maps size in words
    _N_KEYS_DATA_SET_IN_WORDS = 1

    # bytes per word
    _BYTES_PER_WORD = 4

    # bits in a word
    _BITS_IN_A_WORD = 32

    # bit to mask a bit
    _BIT_MASK = 1

    # n region data sets size in words
    _N_REGION_DATA_SETS_IN_WORDS = 1

    # n elements in each key to n atoms map
    _N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP = 2

    _BYTES_PER_FILTER = 12

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

        :param placements: placements
        :param app_graph: the app graph
        :param executable_finder: the executable finder
        :param provenance_file_path: the path to where provenance data items\
                                     is written
        :param transceiver: the SpiNNMan instance
        :param graph_mapper: mapper between application an machine graphs.
        :param read_bit_field_generator_iobuf: bool flag for report
        :param generating_bitfield_report: bool flag for report
        :param default_report_folder: the file path for reports
        :param machine_graph: the machine graph
        :param routing_infos: the key to edge map
        :param generating_bit_field_summary_report: bool flag for making \
        summary report
        :rtype: None
        """

        # progress bar
        progress = ProgressBar(
            len(app_graph.vertices) + 2,
            "Running bitfield generation on chip")

        # get data
        expander_cores = self._calculate_core_data(
            app_graph, graph_mapper, placements, progress, executable_finder)

        # load data
        bit_field_app_id = transceiver.app_id_tracker.get_new_id()
        progress.update(1)

        # run app
        system_control_logic.run_system_application(
            expander_cores, bit_field_app_id, transceiver,
            provenance_file_path, executable_finder,
            read_bit_field_generator_iobuf, self._check_for_success,
            functools.partial(
                self._handle_failure, transceiver=transceiver,
                provenance_file_path=provenance_file_path,
                compressor_app_id=bit_field_app_id,
                executable_finder=executable_finder),
            [CPUState.FINISHED], False, 0)
        # update progress bar
        progress.end()

        # read in bit fields for debugging purposes
        if generating_bitfield_report:
            self._read_back_bit_fields(
                app_graph, graph_mapper, transceiver, placements,
                default_report_folder, self._BIT_FIELD_REPORT_FILENAME)
        if generating_bit_field_summary_report:
            self._read_back_and_summarise_bit_fields(
                app_graph, graph_mapper, transceiver, placements,
                default_report_folder, self._BIT_FIELD_SUMMARY_REPORT_FILENAME)

    def _read_back_and_summarise_bit_fields(
            self, app_graph, graph_mapper, transceiver, placements,
            default_report_folder, bit_field_summary_report_name):
        """ summary report of the bitfields that were generated

        :param app_graph: app graph
        :param graph_mapper: the graph mapper
        :param transceiver: the SPiNNMan instance
        :param placements: The placements
        :param default_report_folder:the file path for where reports are.
        :param bit_field_summary_report_name: the name of the summary file
        :rtype: None
        """
        progress = ProgressBar(
            len(app_graph.vertices),
            "reading back bitfields from chip for summary report")

        chip_packet_count = defaultdict(int)
        chip_redundant_count = defaultdict(int)

        file_path = os.path.join(
            default_report_folder, bit_field_summary_report_name)
        output = open(file_path, "w")

        # read in for each app vertex that would have a bitfield
        for app_vertex in progress.over(app_graph.vertices):
            if isinstance(app_vertex, AbstractPopulationVertex):

                local_total = 0
                local_redundant = 0

                machine_verts = graph_mapper.get_machine_vertices(app_vertex)

                # get machine verts
                for machine_vertex in machine_verts:
                    placement = \
                        placements.get_placement_of_vertex(machine_vertex)

                    # get bitfield address
                    bit_field_address = app_vertex.bit_field_base_address(
                        transceiver, placement)

                    # read how many bitfields there are
                    n_bit_field_entries = struct.unpack(
                        "<I", transceiver.read_memory(
                            placement.x, placement.y, bit_field_address,
                            self._BYTES_PER_WORD))[0]
                    reading_address = bit_field_address + self._BYTES_PER_WORD

                    # read in each bitfield
                    for bit_field_index in range(0, n_bit_field_entries):
                        # master pop key, n words and read pointer
                        (master_pop_key, n_words_to_read, read_pointer) = \
                            struct.unpack(
                                "<III", transceiver.read_memory(
                                    placement.x, placement.y, reading_address,
                                    self._BYTES_PER_FILTER))
                        reading_address += self._BYTES_PER_FILTER

                        # get bitfield words
                        bit_field = struct.unpack(
                            "<{}I".format(n_words_to_read),
                            transceiver.read_memory(
                                placement.x, placement.y, read_pointer,
                                n_words_to_read * WORD_TO_BYTE_MULTIPLIER))

                        n_neurons = n_words_to_read * self._BITS_IN_A_WORD
                        for neuron_id in range(0, n_neurons):
                            if (self._bit_for_neuron_id(
                                    bit_field, neuron_id) == 0):
                                chip_redundant_count[
                                    (placement.x, placement.y)] += 1
                                local_redundant += 1
                            chip_packet_count[(placement.x, placement.y)] += 1
                            local_total += 1
                    output.write(
                        "vertex on {}:{}:{} has total incoming packet count of"
                        " {} and a redundant packet count of {}. Making a "
                        "redundant packet percentage of {}\n".format(
                            placement.x, placement.y, placement.p,
                            local_total, local_redundant,
                            ((100.0 / float(local_total)) * float(
                                local_redundant))))
                    output.flush()

        output.write("\n\n\n")

        # overall summary
        total_packets = 0
        total_redundant_packets = 0
        for (x, y) in chip_packet_count:
            output.write(
                "chip {}:{} has a total incoming packet count of {} and a "
                "redundant packet count of {} given a redundant "
                "percentage of {} \n".format(
                    x, y, chip_packet_count[(x, y)],
                    chip_redundant_count[(x, y)],
                    ((100.0 / float(chip_packet_count[(x, y)])) *
                     float(chip_redundant_count[(x, y)]))))

            total_packets += chip_packet_count[(x, y)]
            total_redundant_packets += chip_redundant_count[(x, y)]
        output.write(
            "overall the application has estimated {} packets flying around "
            "of which {} are redundant at reception. this is a {} percentage "
            "of the packets".format(
                total_packets, total_redundant_packets,
                ((100.0 / float(total_packets)) *
                 float(total_redundant_packets))))
        output.flush()
        output.close()

    def _read_back_bit_fields(
            self, app_graph, graph_mapper, transceiver, placements,
            default_report_folder, bit_field_report_name):
        """ report of the bitfields that were generated

        :param app_graph: app graph
        :param graph_mapper: the graph mapper
        :param transceiver: the SPiNNMan instance
        :param placements: The placements
        :param default_report_folder:the file path for where reports are.
        :param bit_field_report_name: the name of the file
        :rtype: None
        """

        # generate file
        progress = ProgressBar(
            len(app_graph.vertices), "reading back bitfields from chip")

        file_path = os.path.join(default_report_folder, bit_field_report_name)
        output = open(file_path, "w")

        # read in for each app vertex that would have a bitfield
        for app_vertex in progress.over(app_graph.vertices):
            if isinstance(app_vertex, AbstractPopulationVertex):
                machine_verts = graph_mapper.get_machine_vertices(app_vertex)

                # get machine verts
                for machine_vertex in machine_verts:
                    placement = \
                        placements.get_placement_of_vertex(machine_vertex)
                    output.write(
                        "For core {}:{}:{}. Bitfields as follows: \n\n".format(
                            placement.x, placement.y, placement.p))

                    # get bitfield address
                    bit_field_address = app_vertex.bit_field_base_address(
                        transceiver, placement)

                    # read how many bitfields there are
                    n_bit_field_entries = struct.unpack(
                        "<I", transceiver.read_memory(
                            placement.x, placement.y, bit_field_address,
                            self._BYTES_PER_WORD))[0]
                    reading_address = bit_field_address + self._BYTES_PER_WORD

                    # read in each bitfield
                    for bit_field_index in range(0, n_bit_field_entries):

                        # master pop key, n words and read pointer
                        (master_pop_key, n_words_to_read, read_pointer) = \
                            struct.unpack(
                            "<III", transceiver.read_memory(
                                placement.x, placement.y, reading_address,
                                self._BYTES_PER_FILTER))
                        reading_address += self._BYTES_PER_FILTER

                        # get bitfield words
                        bit_field = struct.unpack(
                            "<{}I".format(n_words_to_read),
                            transceiver.read_memory(
                                placement.x, placement.y, read_pointer,
                                n_words_to_read * WORD_TO_BYTE_MULTIPLIER))

                        # put into report
                        n_neurons = n_words_to_read * self._BITS_IN_A_WORD
                        for neuron_id in range(0, n_neurons):
                            output.write(
                                "for key {} neuron id {} has bit {} "
                                "set \n".format(
                                    master_pop_key, neuron_id,
                                    self._bit_for_neuron_id(
                                        bit_field, neuron_id)))
        output.flush()
        output.close()

    def _bit_for_neuron_id(self, bit_field, neuron_id):
        """ locate the bit for the neuron in the bitfield

        :param bit_field: the block of words which represent the bitfield
        :param neuron_id: the neuron id to find the bit in the bitfield
        :return: the bit
        """
        word_id = int(math.floor(neuron_id // self._BITS_IN_A_WORD))
        bit_in_word = neuron_id % self._BITS_IN_A_WORD
        flag = (bit_field[word_id] >> bit_in_word) & self._BIT_MASK
        return flag

    def _calculate_core_data(
            self, app_graph, graph_mapper, placements, progress,
            executable_finder):
        """ gets the data needed for the bit field expander for the machine

        :param app_graph: app graph
        :param graph_mapper: graph mapper between app graph and machine graph
        :param placements: placements
        :param progress: progress bar
        :param executable_finder: where to find the executable
        :return: data and expander cores
        """

        # cores to place bitfield expander
        expander_cores = ExecutableTargets()

        # bit field expander executable file path
        bit_field_expander_path = executable_finder.get_executable_path(
            self._BIT_FIELD_EXPANDER_APLX)

        # locate verts which can have a synaptic matrix to begin with
        for app_vertex in progress.over(app_graph.vertices, False):
            if isinstance(app_vertex, AbstractPopulationVertex):
                machine_verts = graph_mapper.get_machine_vertices(app_vertex)
                for machine_vertex in machine_verts:
                    placement = \
                        placements.get_placement_of_vertex(machine_vertex)

                    # check if the chip being considered already.
                    expander_cores.add_processor(
                        bit_field_expander_path, placement.x, placement.y,
                        placement.p)

        return expander_cores

    def _check_for_success(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """ Goes through the cores checking for cores that have failed to\
            expand the bitfield to the core

        :param executable_targets: cores to load bitfield on
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: path to provenance folder
        :param compressor_app_id: the app id for the compressor c code
        :param executable_finder: executable path finder
        :rtype: None
        """

        for core_subset in executable_targets.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:
                # Read the result from USER0 register
                user_2_base_address = \
                    transceiver.get_user_2_register_address_from_core(p)
                result = struct.unpack(
                    "<I", transceiver.read_memory(
                        x, y, user_2_base_address, self._USER_2_BYTES))[0]

                # The result is 0 if success, otherwise failure
                if result != self._SUCCESS:
                    self._handle_failure(
                        executable_targets, transceiver, provenance_file_path,
                        compressor_app_id, executable_finder)

                    raise SpinnFrontEndException(
                        "The bit field expander on {}, {} failed to complete"
                        .format(x, y))

    @staticmethod
    def _handle_failure(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """handles the state where some cores have failed.

        :param executable_targets: cores which are running the bitfield \
        expander
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :rtype: None
        """
        logger.info("bit field expander has failed")
        iobuf_extractor = ChipIOBufExtractor()
        io_errors, io_warnings = iobuf_extractor(
            transceiver, executable_targets, executable_finder,
            provenance_file_path)
        for warning in io_warnings:
            logger.warning(warning)
        for error in io_errors:
            logger.error(error)
        transceiver.stop_application(compressor_app_id)
        transceiver.app_id_tracker.free_id(compressor_app_id)

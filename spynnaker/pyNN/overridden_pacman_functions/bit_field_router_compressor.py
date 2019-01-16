from collections import defaultdict

import logging

import struct

from spinn_front_end_common.interface.interface_functions import \
    ChipIOBufExtractor
from spinn_front_end_common.mapping_algorithms.\
    on_chip_router_table_compression.mundy_on_chip_router_compression import \
    MundyOnChipRouterCompression
from spinn_front_end_common.utilities.exceptions import SpinnFrontEndException
from spinn_machine import CoreSubsets
from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.abstract_models.\
    abstract_uses_bit_field_filterer import AbstractUsesBitFieldFilter
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.utilities.constants import WORD_TO_BYTE_MULTIPLIER


logger = logging.getLogger(__name__)


class BitFieldRouterCompressor(object):

    # sdram tag the router compressor expects to find there routing tables in
    ROUTING_TABLE_SDRAM_TAG = 1

    # sdram tag for the addresses the router compressor expects to find the /
    # bitfield addresses for the chip.
    BIT_FIELD_ADDRESSES_SDRAM_TAG = 2

    # the successful identifier
    SUCCESS = 0

    # how many header elements are in the region addresses (1, n addresses)
    N_REGIONS_ELEMENT = 1

    # the number of bytes needed to read the user 2 register
    _USER_2_BYTES = 4

    # structs for performance requirements.
    _TWO_WORDS = struct.Struct("<II")

    # binary name
    _ROUTER_TABLE_WITH_BIT_FIELD_APLX = "bit_field_router_compressor.aplx"

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph, graph_mapper,
            placements, executable_finder, read_algorithm_iobuf,
            compress_only_when_needed=True,
            compress_as_much_as_possible=False):
        """ entrance for routing table compression with bit field

        :param routing_tables: routing tables
        :param transceiver: spinnman instance
        :param machine: spinnMachine instance
        :param app_id: app id of the application
        :param provenance_file_path: file path for prov data
        :param machine_graph: machine graph
        :param graph_mapper: mapping between graphs
        :param placements: placements on machine
        :param executable_finder: where are binaries are located
        :param read_algorithm_iobuf: bool flag saying if read iobuf
        :param compress_only_when_needed: bool flag asking if compress only \
        when needed
        :param compress_as_much_as_possible: bool flag asking if should \
        compress as much as possible
        :rtype: None
        """

        # new app id for this simulation
        routing_table_compressor_app_id = \
            transceiver.app_id_tracker.get_new_id()

        progress_bar = ProgressBar(
            total_number_of_things_to_do=(
                len(machine_graph.vertices) + len(
                    routing_tables.routing_tables) + 1),
            string_describing_what_being_progressed=(
                "compressing routing tables and merging in bitfields as "
                "appropriate"))

        # locate data and cores to load binary on
        addresses, cores = self._generate_addresses(
            machine_graph, placements, transceiver, machine, executable_finder,
            progress_bar)

        # load data into sdram
        self._load_data(
            addresses, transceiver, routing_table_compressor_app_id,
            routing_tables, app_id, compress_only_when_needed,
            compress_as_much_as_possible, progress_bar)

        # load and run binaries
        utility_calls.run_system_application(
                cores, app_id, transceiver, provenance_file_path,
                executable_finder, read_algorithm_iobuf,
                self._check_for_success, self._handle_failure,
                [CPUState.FINISHED])

        #complete progress bar
        progress_bar.end()

    def _check_for_success(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """ Goes through the cores checking for cores that have failed to\
            generate the compressed routing tables with bitfield

        :param executable_targets: cores to load router compressor with\
         bitfield on
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
                if result != self.SUCCESS:
                    self._handle_failure(
                        executable_targets, transceiver, provenance_file_path,
                        compressor_app_id, executable_finder)

                    raise SpinnFrontEndException(
                        "The router compressor with bit field on {}, "
                        "{} failed to complete".format(x, y))

    @staticmethod
    def _handle_failure(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """handles the state where some cores have failed.

        :param executable_targets: cores which are running the router \
        compressor with bitfield.
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :rtype: None
        """
        logger.info("routing table compressor with bit field has failed")
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

    def _load_data(
            self, addresses, transceiver, routing_table_compressor_app_id,
            routing_tables, app_id, compress_only_when_needed,
            compress_as_much_as_possible, progress_bar):
        """ load all data onto the chip

        :param addresses: the addresses for bitfields in sdram
        :param transceiver: the spinnMan instance
        :param routing_table_compressor_app_id: the app id for the system app
        :param routing_tables: the routing tables
        :param app_id: the appid of the application
        :param compress_only_when_needed: bool flag asking if compress only \
        when needed
        :param progress_bar: progress bar
        :param compress_as_much_as_possible: bool flag asking if should \
        compress as much as possible
        :rtype: None
        """

        for (chip_x, chip_y) in addresses:
            self.load_address_data(
                addresses, chip_x, chip_y, transceiver,
                routing_table_compressor_app_id)
        for routing_table in routing_tables.routing_tables:
            self.load_routing_table_data(
                routing_table, app_id, transceiver, compress_only_when_needed,
                compress_as_much_as_possible, routing_table_compressor_app_id,
                progress_bar)

    def load_address_data(
            self, addresses, chip_x, chip_y, transceiver,
            routing_table_compressor_app_id):
        """ loads the bitfield addresses space

        :param addresses: the addresses to load
        :param chip_x: the chip x to consider here
        :param chip_y: the chip y to consider here
        :param transceiver: the spinnman instance
        :param routing_table_compressor_app_id: system app id.
        :rtype: None
        """
        # generate address_data
        address_data = self._generate_chip_data(addresses[(chip_x, chip_y)])

        # deduce sdram requirement
        sdram = (
            (len(addresses[(chip_x, chip_y)]) + self.N_REGIONS_ELEMENT) *
            WORD_TO_BYTE_MULTIPLIER)

        # get sdram address on chip
        sdram_address = transceiver.malloc_sdram(
            chip_x, chip_y, sdram, routing_table_compressor_app_id,
            self.BIT_FIELD_ADDRESSES_SDRAM_TAG)

        # write sdram
        transceiver.write_memory(
            chip_x, chip_y, sdram_address, address_data)

    def load_routing_table_data(
            self, routing_table, app_id, transceiver, compress_only_when_needed,
            compress_as_much_as_possible, routing_table_compressor_app_id,
            progress_bar):
        """ loads the routing table data

        :param routing_table: the routing table to load
        :param app_id: application app id
        :param transceiver: spinnman instance
        :param compress_only_when_needed: bool flag asking if compress only \
        when needed
        :param compress_as_much_as_possible: bool flag asking if should \
        compress as much as possible
        :param progress_bar: progress bar
        :param routing_table_compressor_app_id: system app id
        :rtype: None
        """

        routing_table_data = \
            MundyOnChipRouterCompression.build_routing_table_data(
                routing_table, app_id, compress_only_when_needed,
                compress_as_much_as_possible)

        # go to spinnman and ask for a memory region of that size per chip.
        base_address = transceiver.malloc_sdram(
            routing_table.x, routing_table.y, len(routing_table_data),
            routing_table_compressor_app_id, self.ROUTING_TABLE_SDRAM_TAG)

        # write SDRAM requirements per chip
        transceiver.write_memory(
            routing_table.x, routing_table.y, base_address, routing_table_data)

        # update progress bar
        progress_bar.update()

    def _generate_addresses(
            self, machine_graph, placements, transceiver, machine,
            executable_finder, progress_bar):
        """ generates the bitfield sdram addresses

        :param machine_graph: machine graph
        :param placements: placements
        :param transceiver: spinnman instance
        :param machine: spinnmachine instance
        :param progress_bar: the progress bar
        :param executable_finder: binary finder
        :return: addresses and the executable targets to load the router \
        table compressor with bitfield.
        """

        # data holders
        addresses = defaultdict(list)
        cores = CoreSubsets()

        for vertex in progress_bar.over(
                machine_graph.vertices, finish_at_end=False):
            if isinstance(vertex, AbstractUsesBitFieldFilter):
                placement = placements.get_placement_of_vertex(vertex)
                bit_field_sdram_address = vertex.bit_field_base_address(
                    transceiver, placement)
                addresses[placement.x, placement.y].append(
                    bit_field_sdram_address)

                # only add to the cores if the chip hasnt been considered yet
                if not cores.is_chip(placement.x, placement.y):
                    cores.add_processor(
                        placement.x, placement.y,
                        machine.get_chip_at(placement.x, placement.y).
                        get_first_none_monitor_processor())

        # convert core subsets into executable targets
        executable_targets = ExecutableTargets()
        # bit field expander executable file path
        executable_path = executable_finder.get_executable_path(
            self._ROUTER_TABLE_WITH_BIT_FIELD_APLX)
        executable_targets.add_subsets(binary=executable_path, subsets=cores)

        return addresses, executable_targets

    @staticmethod
    def _generate_chip_data(address_list):
        """ generate byte array data for a list of sdram addresses

        :param address_list: the list of sdram addresses
        :return: the byte array
        """
        data = b""
        data += len(address_list)
        for memory_address in address_list:
            data += memory_address
        return data

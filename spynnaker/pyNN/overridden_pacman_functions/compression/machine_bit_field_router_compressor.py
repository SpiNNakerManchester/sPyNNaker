import functools
from collections import defaultdict

import logging

import struct

from pacman.model.routing_tables import MulticastRoutingTables
from spinn_front_end_common.interface.interface_functions import \
    ChipIOBufExtractor
from spinn_front_end_common.mapping_algorithms.\
    on_chip_router_table_compression.mundy_on_chip_router_compression import \
    MundyOnChipRouterCompression
from spinn_front_end_common.utilities.exceptions import SpinnFrontEndException
from spinn_machine import CoreSubsets, Router
from spinn_utilities.progress_bar import ProgressBar
from spinnman.exceptions import SpinnmanInvalidParameterException, \
    SpinnmanUnexpectedResponseCodeException, SpinnmanException
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.exceptions import CantFindSDRAMToUseException
from spynnaker.pyNN.models.abstract_models.\
    abstract_supports_bit_field_generation import \
    AbstractSupportsBitFieldGeneration
from spynnaker.pyNN.models.abstract_models.\
    abstract_supports_bit_field_routing_compression import \
    AbstractSupportsBitFieldRoutingCompression
from spynnaker.pyNN.overridden_pacman_functions.compression.\
    host_bit_field_router_compressor import HostBasedBitFieldRouterCompressor
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.utility_models.synapse_expander.\
    synapse_expander import SYNAPSE_EXPANDER


logger = logging.getLogger(__name__)

# sdram allocation for addresses
SIZE_OF_SDRAM_ADDRESS_IN_BYTES = (17 * 2 * 4) + (3 * 4)


class MachineBitFieldRouterCompressor(object):

    __slots__ = []

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
    _USER_BYTES = 4

    # structs for performance requirements.
    _FOUR_WORDS = struct.Struct("<IIII")

    _THREE_WORDS = struct.Struct("<III")

    _TWO_WORDS = struct.Struct("<II")

    _ONE_WORDS = struct.Struct("<I")

    # binary names
    _BIT_FIELD_SORTER_AND_SEARCH_EXECUTOR_APLX = \
        "bit_field_sorter_and_searcher.aplx"
    _COMPRESSOR_APLX = "bit_field_compressor.aplx"

    _PROGRESS_BAR_TEXT = \
        "on chip compressing routing tables and merging in bitfields as " \
        "appropriate"

    _ON_CHIP_ERROR_MESSAGE = \
        "The router compressor with bit field on {}, {} failed to complete. " \
        "Will execute host based routing compression instead"

    _ON_HOST_WARNING_MESSAGE = \
        "Will be executing compression for {} chips on the host, as they " \
        "failed to complete when running on chip"

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph, graph_mapper,
            placements, executable_finder, read_algorithm_iobuf,
            produce_report, default_report_folder, target_length,
            routing_infos, time_to_try_for_each_iteration, use_timer_cut_off,
            use_expresso, machine_time_step, time_scale_factor,
            no_sync_changes, threshold_percentage,
            compress_only_when_needed=True, use_rob_paul=False,
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
        :param threshold_percentage: the percentage of bitfields to do on chip\
         before its considered a success
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
        print "comp app id is {}".format(routing_table_compressor_app_id)
        print "app app id is {}".format(app_id)

        progress_bar = ProgressBar(
            total_number_of_things_to_do=(
                len(machine_graph.vertices) +
                (len(routing_tables.routing_tables) * 2) + 1),
            string_describing_what_being_progressed=self._PROGRESS_BAR_TEXT)

        # locate data and on_chip_cores to load binary on
        (addresses,
         compressor_with_bit_field_cores,
         bit_field_sorter_executable_path,
         bit_field_compressor_executable_path,
         matrix_addresses_and_size) = self._generate_addresses(
            machine_graph, placements, transceiver, machine, executable_finder,
            progress_bar, graph_mapper)

        # load data into sdram
        on_host_chips = self._load_data(
            addresses, transceiver, routing_table_compressor_app_id,
            routing_tables, app_id, compress_only_when_needed, machine,
            compress_as_much_as_possible, progress_bar,
            compressor_with_bit_field_cores,
            matrix_addresses_and_size, time_to_try_for_each_iteration,
            bit_field_compressor_executable_path,
            bit_field_sorter_executable_path, threshold_percentage)

        # adjust cores to exclude the ones which are going to compress by
        # host processing for compression. but needed to be in the synaptic
        # cores, as it might have overwritten sdram whilst attempting to load
        #  all 3 data blocks.
        expander_chip_cores = self._locate_synaptic_expander_cores(
            compressor_with_bit_field_cores, on_host_chips, executable_finder,
            placements, graph_mapper, bit_field_sorter_executable_path, machine)

        # load and run binaries
        try:
            utility_calls.run_system_application(
                compressor_with_bit_field_cores,
                routing_table_compressor_app_id, transceiver,
                provenance_file_path, executable_finder,
                read_algorithm_iobuf,
                functools.partial(
                    self._check_for_success, host_chips=on_host_chips),
                functools.partial(
                    self._handle_failure_for_bit_field_router_compressor,
                    host_chips=on_host_chips),
                [CPUState.FINISHED], True, no_sync_changes)
        except SpinnmanException:
            self._handle_failure_for_bit_field_router_compressor(
                compressor_with_bit_field_cores, transceiver,
                provenance_file_path, routing_table_compressor_app_id,
                executable_finder, on_host_chips)

        # just rerun the synaptic expander for safety purposes
        #self._rerun_synaptic_cores(
        #    expander_chip_cores, transceiver, provenance_file_path,
        #    executable_finder, True, no_sync_changes)

        # update progress bar to reflect chip compression complete
        progress_bar.update()

        # start the host side compressions if needed
        if len(on_host_chips) != 0:
            logger.warning(
                self._ON_HOST_WARNING_MESSAGE.format(len(on_host_chips)))

            host_compressor = HostBasedBitFieldRouterCompressor()
            threshold_packets = host_compressor.calculate_threshold(
                machine_time_step, time_scale_factor)
            compressed_pacman_router_tables = MulticastRoutingTables()

            for (chip_x, chip_y) in progress_bar.over(on_host_chips, False):
                bit_field_sdram_base_addresses = defaultdict(dict)
                host_compressor.collect_bit_field_sdram_base_addresses(
                        chip_x, chip_y, machine, placements, transceiver,
                        graph_mapper, bit_field_sdram_base_addresses)
                key_to_n_atoms_map = host_compressor.generate_key_to_atom_map(
                    machine_graph, routing_infos, graph_mapper)

                host_compressor.start_compression_selection_process(
                    router_table=routing_tables.get_routing_table_for_chip(
                        chip_x, chip_y),
                    produce_report=produce_report,
                    report_folder_path=host_compressor.generate_report_path(
                        default_report_folder),
                    bit_field_sdram_base_addresses=(
                        bit_field_sdram_base_addresses),
                    transceiver=transceiver, machine_graph=machine_graph,
                    placements=placements, machine=machine,
                    graph_mapper=graph_mapper,
                    target_length=target_length,
                    time_to_try_for_each_iteration=(
                        time_to_try_for_each_iteration),
                    use_timer_cut_off=use_timer_cut_off,
                    use_expresso=use_expresso, use_rob_paul=use_rob_paul,
                    threshold_packets=threshold_packets,
                    key_to_n_atoms_map=key_to_n_atoms_map,
                    compressed_pacman_router_tables=(
                        compressed_pacman_router_tables))

            # load host compressed routing tables
            for table in compressed_pacman_router_tables.routing_tables:
                if (not machine.get_chip_at(table.x, table.y).virtual
                        and table.multicast_routing_entries):
                    transceiver.load_multicast_routes(
                        table.x, table.y, table.multicast_routing_entries,
                        app_id=app_id)

        # complete progress bar
        progress_bar.end()

    @staticmethod
    def _locate_synaptic_expander_cores(
            cores, run_on_host, executable_finder, placements, graph_mapper,
            bit_field_router_compressor_executable_path, machine):
        """ removes host based cores for synaptic matrix regeneration
        
        :param cores: the cores for everything
        :param run_on_host: the chips that had to be ran on host
        :param executable_finder: way to get binary path
        :param bit_field_router_compressor_executable_path: the path to the \
            routing compressor with bitfield
        :param graph_mapper: mapping between graphs
        :param machine: spiNNMachine instance.
        :return: new targets for synaptic expander
        """
        new_cores = ExecutableTargets()

        # locate expander executable path
        expander_executable_path = executable_finder.get_executable_path(
            SYNAPSE_EXPANDER)

        # get the cores for the router compressor with bitfield
        core_subsets = cores.get_cores_for_binary(
            bit_field_router_compressor_executable_path)

        # if any ones are going to be ran on host, ignore them from the new
        # core setup
        for core_subset in core_subsets.core_subsets:
            key = (core_subset.x, core_subset.y)
            if key not in run_on_host:
                chip = machine.get_chip_at(core_subset.x, core_subset.y)
                for processor_id in range(0, chip.n_processors):
                    if placements.is_processor_occupied(
                            core_subset.x, core_subset.y, processor_id):
                        vertex = placements.get_vertex_on_processor(
                            core_subset.x, core_subset.y, processor_id)
                        app_vertex = graph_mapper.get_application_vertex(vertex)
                        if isinstance(
                                app_vertex, AbstractSupportsBitFieldGeneration):
                            if app_vertex.gen_on_machine(
                                    graph_mapper.get_slice(vertex)):
                                new_cores.add_processor(
                                    expander_executable_path, core_subset.x,
                                    core_subset.y, processor_id)
        return new_cores

    def _rerun_synaptic_cores(
            self, synaptic_expander_rerun_cores, transceiver,
            provenance_file_path, executable_finder, needs_sync_barrier,
            no_sync_changes):
        """ reruns the synaptic expander

        :param synaptic_expander_rerun_cores: the cores to rerun the synaptic /
        matrix generator for
        :param transceiver: spinnman instance
        :param provenance_file_path: prov file path
        :param executable_finder: finder of binary file paths
        :rtype: None
        """
        if synaptic_expander_rerun_cores.total_processors != 0:
            logger.info("rerunning synaptic expander")
            expander_app_id = transceiver.app_id_tracker.get_new_id()
            utility_calls.run_system_application(
                synaptic_expander_rerun_cores, expander_app_id, transceiver,
                provenance_file_path, executable_finder, True, None,
                self._handle_failure_for_synaptic_expander_rerun,
                [CPUState.FINISHED], needs_sync_barrier, no_sync_changes)

    def _check_for_success(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder, host_chips):
        """ Goes through the cores checking for cores that have failed to\
            generate the compressed routing tables with bitfield

        :param executable_targets: cores to load router compressor with\
         bitfield on
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: path to provenance folder
        :param compressor_app_id: the app id for the compressor c code
        :param host_chips: the chips which need to be ran on host. 
        :param executable_finder: executable path finder
        :rtype: None
        """
        for core_subset in executable_targets.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:

                # Read the result from USER1 register
                user_1_base_address = \
                    transceiver.get_user_1_register_address_from_core(p)
                result = struct.unpack(
                    "<I", transceiver.read_memory(
                        x, y, user_1_base_address, self._USER_BYTES))[0]

                if result != self.SUCCESS:
                    self._call_iobuf_and_clean_up(
                        executable_targets, transceiver, provenance_file_path,
                        compressor_app_id, executable_finder)
                    if (x, y) not in host_chips:
                        host_chips.append((x, y))
                    raise SpinnFrontEndException(
                        self._ON_CHIP_ERROR_MESSAGE.format(x, y))

    def _handle_failure_for_bit_field_router_compressor(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder, host_chips):
        """handles the state where some cores have failed.

        :param executable_targets: cores which are running the router \
        compressor with bitfield.
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :param host_chips: chips which need host based compression
        :rtype: None
        """
        logger.info(
            "on chip routing table compressor with bit field has failed")
        for core_subset in executable_targets.all_core_subsets:
            if (core_subset.x, core_subset.y) not in host_chips:
                host_chips.append((core_subset.x, core_subset.y))

    def _handle_failure_for_synaptic_expander_rerun(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """handles the state where some cores have failed.

        :param executable_targets: cores which are running the router \
        compressor with bitfield.
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :rtype: None
        """
        logger.info("rerunning of the synaptic expander has failed")
        self._call_iobuf_and_clean_up(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder)

    @staticmethod
    def _call_iobuf_and_clean_up(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """handles the reading of iobuf and cleaning the cores off the machine

        :param executable_targets: cores which are running the router \
        compressor with bitfield.
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: provenance file path
        :param executable_finder: executable finder
        :rtype: None
        """
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
            routing_tables, app_id, compress_only_when_needed, machine,
            compress_as_much_as_possible, progress_bar, cores,
            matrix_addresses_and_size, time_per_iteration,
            bit_field_compressor_executable_path,
            bit_field_sorter_executable_path, threshold_percentage):
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
        :param cores: the cores that compressor will run on
        :param matrix_addresses_and_size: dict of chips to regeneration 
        sdram and size for exploitation
        :param bit_field_compressor_executable_path: the path to the \
        compressor binary path
        :param bit_field_sorter_executable_path: the path to the sorter binary
        :return: the list of tuples saying which chips this will need to use \ 
        host compression, as the malloc failed.
        :rtype: list of tuples saying which chips this will need to use host \
        compression, as the malloc failed.
        """

        run_by_host = list()
        for (chip_x, chip_y) in addresses:
            table = routing_tables.get_routing_table_for_chip(chip_x, chip_y)
            if (table is not None and not machine.get_chip_at(
                    table.x, table.y).virtual):
                try:
                    self._load_routing_table_data(
                        table, app_id, transceiver,
                        routing_table_compressor_app_id, progress_bar, cores,
                        matrix_addresses_and_size[(table.x, table.y)])

                    self._load_address_data(
                        addresses, chip_x, chip_y, transceiver, 
                        routing_table_compressor_app_id,
                        cores, matrix_addresses_and_size[(table.x, table.y)],
                        bit_field_compressor_executable_path,
                        bit_field_sorter_executable_path, threshold_percentage)

                    self._load_usable_sdram(
                        matrix_addresses_and_size[(table.x, table.y)], chip_x,
                        chip_y, transceiver, routing_table_compressor_app_id,
                        cores)

                    self._load_compressor_data(
                        chip_x, chip_y, time_per_iteration, transceiver,
                        bit_field_compressor_executable_path, cores,
                        compress_only_when_needed, compress_as_much_as_possible)
                except CantFindSDRAMToUseException:
                    run_by_host.append((chip_x, chip_y))

        return run_by_host

    def _load_compressor_data(
            self, chip_x, chip_y, time_per_iteration, transceiver,
            bit_field_compressor_executable_path, cores,
            compress_only_when_needed, compress_as_much_as_possible):
        """ updates the user1 address for the compressor cores so they can 
        set the time per attempt
        
        :param chip_x: chip x coord
        :param chip_y: chip y coord
        :param time_per_iteration: time per attempt of compression
        :param transceiver: SpiNNMan instance
        :param bit_field_compressor_executable_path: path for the compressor \
        binary 
        :param compress_only_when_needed: bool flag asking if compress only \
        when needed
        :param compress_as_much_as_possible: bool flag asking if should \
        compress as much as possible
        :param cores: the executable targets
        :rtype: None 
        """
        compressor_cores = cores.get_cores_for_binary(
            bit_field_compressor_executable_path)
        for processor_id in compressor_cores.get_core_subset_for_chip(
                chip_x, chip_y).processor_ids:
            user1_base_address = \
                transceiver.get_user_1_register_address_from_core(processor_id)
            user2_base_address = \
                transceiver.get_user_2_register_address_from_core(processor_id)
            user3_base_address = \
                transceiver.get_user_3_register_address_from_core(processor_id)
            transceiver.write_memory(
                chip_x, chip_y, user1_base_address,
                self._ONE_WORDS.pack(time_per_iteration), self._USER_BYTES)
            transceiver.write_memory(
                chip_x, chip_y, user2_base_address,
                self._ONE_WORDS.pack(compress_only_when_needed),
                self._USER_BYTES)
            transceiver.write_memory(
                chip_x, chip_y, user3_base_address,
                self._ONE_WORDS.pack(compress_as_much_as_possible),
                self._USER_BYTES)

    def _load_usable_sdram(
            self, matrix_addresses_and_size, chip_x, chip_y, transceiver,
            routing_table_compressor_app_id, cores):
        """
        
        :param matrix_addresses_and_size: sdram usable and sizes
        :param chip_x: the chip x to consider here
        :param chip_y: the chip y to consider here
        :param transceiver: the spinnman instance
        :param routing_table_compressor_app_id: system app id.
        :param cores: the cores that compressor will run on
        :rtype: None
        """
        address_data = \
            self._generate_chip_matrix_data(matrix_addresses_and_size)

        # get sdram address on chip
        try:
            sdram_address = transceiver.malloc_sdram(
                chip_x, chip_y, len(address_data),
                routing_table_compressor_app_id)
        except (SpinnmanInvalidParameterException,
                SpinnmanUnexpectedResponseCodeException):
            sdram_address = self._steal_from_matrix_addresses(
                matrix_addresses_and_size, len(address_data))

        # write sdram
        transceiver.write_memory(
            chip_x, chip_y, sdram_address, address_data, len(address_data))

        # get the only processor on the chip
        processor_id = list(cores.all_core_subsets.get_core_subset_for_chip(
            chip_x, chip_y).processor_ids)[0]

        # update user 2 with location
        user_3_base_address = \
            transceiver.get_user_3_register_address_from_core(processor_id)
        transceiver.write_memory(
            chip_x, chip_y, user_3_base_address,
            self._ONE_WORDS.pack(sdram_address), self._USER_BYTES)

    def _generate_chip_matrix_data(self, list_of_sizes_and_address):
        """ generate the data for the chip matrix data
        
        :param list_of_sizes_and_address: list of sdram addresses and sizes
        :return: byte array of data
        """
        data = b""
        data += self._ONE_WORDS.pack(len(list_of_sizes_and_address))
        for (memory_address, size) in list_of_sizes_and_address:
            data += self._TWO_WORDS.pack(memory_address, size)
        return data

    def _load_address_data(
            self, addresses, chip_x, chip_y, transceiver,
            routing_table_compressor_app_id, cores, matrix_addresses_and_size,
            bit_field_compressor_executable_path,
            bit_field_sorter_executable_path, threshold_percentage):
        """ loads the bitfield addresses space

        :param addresses: the addresses to load
        :param chip_x: the chip x to consider here
        :param chip_y: the chip y to consider here
        :param transceiver: the spinnman instance
        :param routing_table_compressor_app_id: system app id.
        :param cores: the cores that compressor will run on
        :param bit_field_compressor_executable_path: the path to the \
        compressor binary path
        :param bit_field_sorter_executable_path: the path to the sorter binary
        :rtype: None
        """
        # generate address_data
        address_data = self._generate_chip_data(
            addresses[(chip_x, chip_y)],
            cores.get_cores_for_binary(
                bit_field_compressor_executable_path).get_core_subset_for_chip(
                    chip_x, chip_y),
            threshold_percentage)

        # get sdram address on chip
        try:
            sdram_address = transceiver.malloc_sdram(
                chip_x, chip_y, len(address_data),
                routing_table_compressor_app_id)
        except (SpinnmanInvalidParameterException,
                SpinnmanUnexpectedResponseCodeException):
            sdram_address = self._steal_from_matrix_addresses(
                matrix_addresses_and_size, len(address_data))

        # write sdram
        transceiver.write_memory(
            chip_x, chip_y, sdram_address, address_data, len(address_data))

        # get the only processor on the chip
        sorter_cores = cores.get_cores_for_binary(
            bit_field_sorter_executable_path)
        processor_id = list(sorter_cores.get_core_subset_for_chip(
            chip_x, chip_y).processor_ids)[0]

        # update user 2 with location
        user_2_base_address = \
            transceiver.get_user_2_register_address_from_core(processor_id)
        transceiver.write_memory(
            chip_x, chip_y, user_2_base_address,
            self._ONE_WORDS.pack(sdram_address), self._USER_BYTES)

    def _load_routing_table_data(
            self, table, app_id, transceiver,
            routing_table_compressor_app_id, progress_bar, cores,
            matrix_addresses_and_size):
        """ loads the routing table data

        :param table: the routing table to load
        :param app_id: application app id
        :param transceiver: spinnman instance
        :param progress_bar: progress bar
        :param routing_table_compressor_app_id: system app id
        :param cores: the cores that the compressor going to run on
        :rtype: None
        :raises CantFindSDRAMToUse when sdram is not malloc-ed or stolen
        """

        routing_table_data = self._build_routing_table_data(app_id, table)

        # go to spinnman and ask for a memory region of that size per chip.
        try:
            base_address = transceiver.malloc_sdram(
                table.x, table.y, len(routing_table_data),
                routing_table_compressor_app_id)
        except (SpinnmanInvalidParameterException,
                SpinnmanUnexpectedResponseCodeException):
            base_address = self._steal_from_matrix_addresses(
                matrix_addresses_and_size, len(routing_table_data))

        print "user 1 should point at {}".format(base_address)
        # write SDRAM requirements per chip
        transceiver.write_memory(
            table.x, table.y, base_address, routing_table_data)

        # get the only processor on the chip
        processor_id = list(cores.all_core_subsets.get_core_subset_for_chip(
            table.x, table.y).processor_ids)[0]

        # update user 1 with location
        user_1_base_address = \
            transceiver.get_user_1_register_address_from_core(processor_id)
        transceiver.write_memory(
            table.x, table.y, user_1_base_address,
            self._ONE_WORDS.pack(base_address), self._USER_BYTES)

        # update progress bar
        progress_bar.update()

    def _build_routing_table_data(self, app_id, routing_table):
        """ builds routing data as needed for the compressor cores
        
        :param app_id: appid of the application to load entries with
        :param routing_table: the uncompressed routing table
        :return: data array
        """
        data = b''
        data += self._TWO_WORDS.pack(app_id, routing_table.number_of_entries)

        for entry in routing_table.multicast_routing_entries:
            data += self._FOUR_WORDS.pack(
                entry.routing_entry_key, entry.mask,
                Router.convert_routing_table_entry_to_spinnaker_route(entry),
                MundyOnChipRouterCompression.make_source_hack(entry))
        return bytearray(data)

    @staticmethod
    def _steal_from_matrix_addresses(matrix_addresses_and_size, size_to_steal):
        """ steals memory from synaptic matrix as needed
        
        :param matrix_addresses_and_size: matrix addresses and sizes
        :param size_to_steal: size needed to steal from matrix's.
        :return: address to start steal from
        :raises CantFindSDRAMToUseException: when no space is big enough to /
        steal from.
        """
        for pos, (base_address, size) in enumerate(matrix_addresses_and_size):
            if size >= size_to_steal:
                new_size = size - size_to_steal
                matrix_addresses_and_size[pos] = (base_address, new_size)
                return base_address
        raise CantFindSDRAMToUseException()

    def _generate_addresses(
            self, machine_graph, placements, transceiver, machine,
            executable_finder, progress_bar, graph_mapper):
        """ generates the bitfield sdram addresses

        :param machine_graph: machine graph
        :param placements: placements
        :param transceiver: spinnman instance
        :param machine: spinnmachine instance
        :param progress_bar: the progress bar
        :param: graph_mapper: mapping between graphs
        :param executable_finder: binary finder
        :return: region_addresses and the executable targets to load the \
        router table compressor with bitfield. and the executable path\ and 
        the synaptic matrix spaces to corrupt
        """

        # data holders
        region_addresses = defaultdict(list)
        synaptic_matrix_addresses_and_sizes = defaultdict(list)
        bit_field_sorter_cores = CoreSubsets()
        bit_field_compressor_cores = CoreSubsets()

        for vertex in progress_bar.over(
                machine_graph.vertices, finish_at_end=False):

            app_vertex = graph_mapper.get_application_vertex(vertex)
            if isinstance(
                    app_vertex, AbstractSupportsBitFieldRoutingCompression):
                placement = placements.get_placement_of_vertex(vertex)

                # store the region sdram address's
                bit_field_sdram_address = app_vertex.bit_field_base_address(
                    transceiver, placement)
                print bit_field_sdram_address
                key_to_atom_map = \
                    app_vertex.key_to_atom_map_region_base_address(
                        transceiver, placement)
                region_addresses[placement.x, placement.y].append(
                    (bit_field_sdram_address, key_to_atom_map, placement.p))

                # store the available space from the matrix to steal
                (address, size) = \
                    app_vertex.synaptic_expander_base_address_and_size(
                        transceiver, placement)
                if size != 0:
                    synaptic_matrix_addresses_and_sizes[
                        placement.x, placement.y].append((address, size))

                # only add to the cores if the chip has not been considered yet
                if not bit_field_sorter_cores.is_chip(placement.x, placement.y):
                    # add 1 core to the sorter, and the rest to compressors
                    sorter = None
                    for processor in machine.get_chip_at(
                            placement.x, placement.y).processors:
                        if not processor.is_monitor:
                            if sorter is None:
                                sorter = processor
                                bit_field_sorter_cores.add_processor(
                                    placement.x, placement.y,
                                    processor.processor_id)
                            else:
                                bit_field_compressor_cores.add_processor(
                                    placement.x, placement.y,
                                    processor.processor_id)

        # convert core subsets into executable targets
        executable_targets = ExecutableTargets()
        # bit field expander executable file path
        bit_field_sorter_executable_path = \
            executable_finder.get_executable_path(
                self._BIT_FIELD_SORTER_AND_SEARCH_EXECUTOR_APLX)
        bit_field_compressor_executable_path = \
            executable_finder.get_executable_path(self._COMPRESSOR_APLX)
        executable_targets.add_subsets(
            binary=bit_field_sorter_executable_path,
            subsets=bit_field_sorter_cores)
        executable_targets.add_subsets(
            binary=bit_field_compressor_executable_path,
            subsets=bit_field_compressor_cores)

        return (region_addresses, executable_targets,
                bit_field_sorter_executable_path,
                bit_field_compressor_executable_path,
                synaptic_matrix_addresses_and_sizes)

    def _generate_chip_data(self, address_list, cores, threshold_percentage):
        """ generate byte array data for a list of sdram addresses and 
        finally the time to run per compression iteration

        :param address_list: the list of sdram addresses
        :param cores: compressor cores on this chip. 
        :return: the byte array
        """
        data = b""
        data += self._ONE_WORDS.pack(threshold_percentage)
        data += self._ONE_WORDS.pack(len(address_list))
        for (bit_field, key_to_atom, processor_id) in address_list:
            data += self._THREE_WORDS.pack(
                bit_field, key_to_atom, processor_id)
        data += self._ONE_WORDS.pack(len(cores))
        compression_cores = list(cores.processor_ids)
        data += struct.pack("<{}I".format(len(cores)), *compression_cores)
        #compression_cores = list(cores.processor_ids)[0:1]
        #data += self._ONE_WORDS.pack(len(compression_cores))
        #data += struct.pack("<{}I".format(len(compression_cores)), *compression_cores)
        return data

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
from spinn_machine import CoreSubsets
from spinn_utilities.progress_bar import ProgressBar
from spinnman.exceptions import SpinnmanInvalidParameterException, \
    SpinnmanUnexpectedResponseCodeException
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.abstract_models.\
    abstract_uses_bit_field_filterer import AbstractUsesBitFieldFilter
from spynnaker.pyNN.overridden_pacman_functions.compression.\
    host_bit_field_router_compressor import HostBasedBitFieldRouterCompressor
from spynnaker.pyNN.utilities import utility_calls


logger = logging.getLogger(__name__)


class MachineBitFieldRouterCompressor(object):

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
    _TWO_WORDS = struct.Struct("<II")

    _ONE_WORDS = struct.Struct("<I")

    # binary name
    _ROUTER_TABLE_WITH_BIT_FIELD_APLX = "bit_field_router_compressor.aplx"

    def __call__(
            self, routing_tables, transceiver, machine, app_id,
            provenance_file_path, machine_graph, graph_mapper,
            placements, executable_finder, read_algorithm_iobuf,
            produce_report, default_report_folder, target_length,
            routing_infos, time_to_try_for_each_iteration, use_timer_cut_off,
            use_expresso, use_rob_paul, machine_time_step, time_scale_factor,
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

        # locate data and on_chip_cores to load binary on
        (addresses, on_chip_cores, executable_path,
         matrix_addresses_and_size) = self._generate_addresses(
            machine_graph, placements, transceiver, machine, executable_finder,
            progress_bar, graph_mapper)

        # load data into sdram
        on_host_chips = self._load_data(
            addresses, transceiver, routing_table_compressor_app_id,
            routing_tables, app_id, compress_only_when_needed, machine,
            compress_as_much_as_possible, progress_bar, on_chip_cores,
            matrix_addresses_and_size)

        # adjust cores to exclude the ones which are going to compress by
        # host processing
        if len(on_host_chips) != 0:
            on_chip_cores = self._regenerate_cores(
                on_chip_cores, on_host_chips, executable_path)

        # load and run binaries
        utility_calls.run_system_application(
            on_chip_cores, routing_table_compressor_app_id, transceiver,
            provenance_file_path, executable_finder,
            read_algorithm_iobuf, self._check_for_success,
            self._handle_failure_for_bit_field_router_compressor,
            [CPUState.FINISHED])

        # just rerun the synaptic expander for safety purposes
        self._rerun_synaptic_cores(
            on_chip_cores, transceiver, provenance_file_path, executable_finder)

        # update progress bar to reflect chip compression complete
        progress_bar.update()

        # start the host side compressions if needed

        if len(on_host_chips) != 0:
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
    def _regenerate_cores(cores, run_on_host, executable_path):
        new_cores = ExecutableTargets()

        core_subsets = cores.get_cores_for_binary(executable_path)
        for core_subset in core_subsets.core_subsets:
            key = (core_subset.x, core_subset.y)
            if key not in run_on_host:
                for processor_id in core_subset.processor_ids:
                    new_cores.add_processor(
                        executable_path, core_subset.x, core_subset.y,
                        processor_id)
        return new_cores

    def _rerun_synaptic_cores(
            self, synaptic_expander_rerun_cores, transceiver,
            provenance_file_path, executable_finder):
        """ reruns the synaptic expander

        :param synaptic_expander_rerun_cores: the cores to rerun the synaptic /
        matrix generator for
        :param transceiver: spinnman instance
        :param provenance_file_path: prov file path
        :param executable_finder: finder of binary file paths
        :rtype: None
        """
        expander_app_id = transceiver.app_id_tracker.get_new_id()
        utility_calls.run_system_application(
            synaptic_expander_rerun_cores, expander_app_id, transceiver,
            provenance_file_path, executable_finder, True, None,
            self._handle_failure_for_synaptic_expander_rerun,
            [CPUState.FINISHED])

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

                # Read the result from USER1 register
                user_2_base_address = \
                    transceiver.get_user_2_register_address_from_core(p)
                result = struct.unpack(
                    "<I", transceiver.read_memory(
                        x, y, user_2_base_address, self._USER_BYTES))[0]

                # The result is 0 if success, otherwise failure
                if result != self.SUCCESS:
                    self._handle_failure_for_bit_field_router_compressor(
                        executable_targets, transceiver, provenance_file_path,
                        compressor_app_id, executable_finder)

                    raise SpinnFrontEndException(
                        "The router compressor with bit field on {}, "
                        "{} failed to complete".format(x, y))

    def _handle_failure_for_bit_field_router_compressor(
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
        logger.info("routing table compressor with bit field has failed")
        self._call_iobuf_and_clean_up(
            executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder)

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
            matrix_addresses_and_size):
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
                    self._load_usable_sdram(
                        matrix_addresses_and_size, chip_x, chip_y, transceiver,
                        routing_table_compressor_app_id, cores)

                    self._load_address_data(
                        addresses, chip_x, chip_y, transceiver,
                        routing_table_compressor_app_id, cores)

                    self._load_routing_table_data(
                        table, app_id, transceiver,
                        compress_only_when_needed, compress_as_much_as_possible,
                        routing_table_compressor_app_id, progress_bar, cores)
                except SpinnmanInvalidParameterException:
                    run_by_host.append((chip_x, chip_y))
                except SpinnmanUnexpectedResponseCodeException:
                    run_by_host.append((chip_x, chip_y))
        return run_by_host

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
        address_data = self._generate_chip_matrix_data(
            matrix_addresses_and_size[(chip_x, chip_y)])

        # get sdram address on chip
        sdram_address = transceiver.malloc_sdram(
            chip_x, chip_y, len(address_data), routing_table_compressor_app_id)

        # write sdram
        transceiver.write_memory(
            chip_x, chip_y, sdram_address, address_data, len(address_data))

        # get the only processor on the chip
        processor_id = cores.all_core_subsets.get_core_subset_for_chip(
            chip_x, chip_y).processor_ids[0]

        # update user 2 with location
        user_3_base_address = \
            transceiver.get_user_3_register_address_from_core(processor_id)
        transceiver.write_memory(
            chip_x, chip_y, user_3_base_address,
            self._ONE_WORDS.pack(sdram_address), self._USER_BYTES)

    def _generate_chip_matrix_data(self, list_of_sizes_and_address):
        data = b""
        data += self._ONE_WORDS.pack(len(list_of_sizes_and_address))
        for (memory_address, size) in list_of_sizes_and_address:
            data += self._TWO_WORDS.pack(memory_address, size)
        return data

    def _load_address_data(
            self, addresses, chip_x, chip_y, transceiver,
            routing_table_compressor_app_id, cores):
        """ loads the bitfield addresses space

        :param addresses: the addresses to load
        :param chip_x: the chip x to consider here
        :param chip_y: the chip y to consider here
        :param transceiver: the spinnman instance
        :param routing_table_compressor_app_id: system app id.
        :param cores: the cores that compressor will run on
        :rtype: None
        """
        # generate address_data
        address_data = self._generate_chip_data(addresses[(chip_x, chip_y)])

        # get sdram address on chip
        sdram_address = transceiver.malloc_sdram(
            chip_x, chip_y, len(address_data), routing_table_compressor_app_id)

        # write sdram
        transceiver.write_memory(
            chip_x, chip_y, sdram_address, address_data, len(address_data))

        # get the only processor on the chip
        processor_id = cores.all_core_subsets.get_core_subset_for_chip(
            chip_x, chip_y).processor_ids[0]

        # update user 2 with location
        user_2_base_address = \
            transceiver.get_user_2_register_address_from_core(processor_id)
        transceiver.write_memory(
            chip_x, chip_y, user_2_base_address,
            self._ONE_WORDS.pack(sdram_address), self._USER_BYTES)

    def _load_routing_table_data(
            self, routing_table, app_id, transceiver,
            compress_only_when_needed, compress_as_much_as_possible,
            routing_table_compressor_app_id, progress_bar, cores):
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
        :param cores: the cores that the compressor going to run on
        :rtype: None
        """

        routing_table_data = \
            MundyOnChipRouterCompression.build_routing_table_data(
                routing_table, app_id, compress_only_when_needed,
                compress_as_much_as_possible)

        # go to spinnman and ask for a memory region of that size per chip.
        base_address = None
        try:
            base_address = transceiver.malloc_sdram(
                routing_table.x, routing_table.y, len(routing_table_data),
                routing_table_compressor_app_id)
        except SpinnmanInvalidParameterException:
            pass

        # write SDRAM requirements per chip
        transceiver.write_memory(
            routing_table.x, routing_table.y, base_address, routing_table_data)

        # get the only processor on the chip
        processor_id = cores.all_core_subsets.get_core_subset_for_chip(
            routing_table.x, routing_table.y).processor_ids[0]

        # update user 1 with location
        user_1_base_address = \
            transceiver.get_user_1_register_address_from_core(processor_id)
        transceiver.write_memory(
            routing_table.x, routing_table.y, user_1_base_address,
            self._ONE_WORDS.pack(base_address), self._USER_BYTES)

        # update progress bar
        progress_bar.update()

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
        :return: bit_field_addresses and the executable targets to load the \
        router table compressor with bitfield. and the executable path\ and 
        the synaptic matrix spaces to corrupt
        """

        # data holders
        bit_fieldaddresses = defaultdict(list)
        synaptic_matrix_addresses_and_sizes = defaultdict(list)
        cores = CoreSubsets()

        for vertex in progress_bar.over(
                machine_graph.vertices, finish_at_end=False):

            app_vertex = graph_mapper.get_application_vertex(vertex)
            if isinstance(app_vertex, AbstractUsesBitFieldFilter):
                placement = placements.get_placement_of_vertex(vertex)
                bit_field_sdram_address = app_vertex.bit_field_base_address(
                    transceiver, placement)
                bit_fieldaddresses[placement.x, placement.y].append(
                    bit_field_sdram_address)
                synaptic_matrix_addresses_and_sizes[
                    placement.x, placement.y].append(
                        app_vertex.synaptic_expander_base_address_and_size(
                            transceiver, placement))

                # only add to the cores if the chip hasnt been considered yet
                if not cores.is_chip(placement.x, placement.y):
                    cores.add_processor(
                        placement.x, placement.y,
                        machine.get_chip_at(placement.x, placement.y).
                        get_first_none_monitor_processor().processor_id)

        # convert core subsets into executable targets
        executable_targets = ExecutableTargets()
        # bit field expander executable file path
        executable_path = executable_finder.get_executable_path(
            self._ROUTER_TABLE_WITH_BIT_FIELD_APLX)
        executable_targets.add_subsets(binary=executable_path, subsets=cores)

        return (bit_fieldaddresses, executable_targets, executable_path,
                synaptic_matrix_addresses_and_sizes)

    def _generate_chip_data(self, address_list):
        """ generate byte array data for a list of sdram addresses

        :param address_list: the list of sdram addresses
        :return: the byte array
        """
        data = b""
        data += self._ONE_WORDS.pack(len(address_list))
        for memory_address in address_list:
            data += self._ONE_WORDS.pack(memory_address)
        return data

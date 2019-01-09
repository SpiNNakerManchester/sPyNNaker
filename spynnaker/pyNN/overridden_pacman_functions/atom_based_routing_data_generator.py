import math

from spinn_front_end_common.interface.interface_functions import \
    ChipIOBufExtractor
from spinn_front_end_common.utilities.exceptions import SpinnFrontEndException

from spinn_utilities.progress_bar import ProgressBar

from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState

from spynnaker.pyNN.models.abstract_models.\
    abstract_uses_population_table_and_synapses import \
    AbstractUsesPopulationTableAndSynapses

import struct
import logging
import os

from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)


class SpynnakerAtomBasedRoutingDataGenerator(object):
    """ Executes bitfield and routing table entries for atom based routing
    """

    __slots__ = ()

    # the sdram tag being used here
    _SDRAM_TAG = 2

    # flag which states that the binary finished cleanly.
    _SUCCESS = 0

    # the number of bytes needed to read the user2 register
    _USER_2_BYTES = 4

    # master pop, synaptic matrix, bitfield base addresses
    _N_ELEMENTS_PER_REGION_ELEMENT = 5

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

    # bit field report file name
    _BIT_FIELD_REPORT_FILENAME = "generated_bit_fields.rpt"

    # structs for performance requirements.
    _ONE_WORDS = struct.Struct("<I")
    _TWO_WORDS = struct.Struct("<II")
    _FOUR_WORDS = struct.Struct("<IIII")

    # binary name
    _BIT_FIELD_EXPANDER_APLX = "bit_field_expander.aplx"

    def __call__(
            self, placements, app_graph, executable_finder,
            provenance_file_path, machine, transceiver, graph_mapper,
            read_bit_field_generator_iobuf, generating_bitfield_report,
            default_report_folder, machine_graph, routing_infos):
        """ loads and runs the bit field generator on chip

        :param placements: placements
        :param app_graph: the app graph
        :param executable_finder: the executable finder
        :param provenance_file_path: the path to where provenance data items\
                                     is written
        :param machine: the SpiNNMachine instance
        :param transceiver: the SpiNNMan instance
        :param graph_mapper: mapper between application an machine graphs.
        :param read_bit_field_generator_iobuf: bool flag for report
        :param generating_bitfield_report: bool flag for report
        :param default_report_folder: the file path for reports
        :param machine_graph: the machine graph
        :param routing_infos: the key to edge map
        :rtype: None
        """

        # progress bar
        progress = ProgressBar(
            len(app_graph.vertices) + 2,
            "Running bitfield generation on chip")

        # get data
        data_address, expander_cores = self._calculate_core_data(
            app_graph, graph_mapper, transceiver, placements, machine,
            progress, executable_finder, machine_graph, routing_infos)

        # load data
        bit_field_app_id = self._allocate_sdram_and_fill_in(
            data_address, transceiver)
        progress.update(1)

        # run app
        self._run_app(
            expander_cores, bit_field_app_id, transceiver,
            provenance_file_path, executable_finder,
            read_bit_field_generator_iobuf)

        # read in bit fields for debugging purposes
        if generating_bitfield_report:
            self._read_back_bit_fields(
                app_graph, graph_mapper, transceiver, placements,
                default_report_folder)

        # update progress bar
        progress.end()

    def _read_back_bit_fields(
            self, app_graph, graph_mapper, transceiver, placements,
            default_report_folder):
        """ report of the bitfields that were generated

        :param app_graph: app graph
        :param graph_mapper: the graph mapper
        :param transceiver: the SPiNNMan instance
        :param placements: The placements
        :param default_report_folder:the file path for where reports are.
        :rtype: None 
        """

        # generate file
        file_path = os.path.join(
            default_report_folder, self._BIT_FIELD_REPORT_FILENAME)
        output = open(file_path, "w")

        # read in for each app vertex that would have a bitfield
        for app_vertex in app_graph.vertices:
            if isinstance(app_vertex, AbstractUsesPopulationTableAndSynapses):
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

                        # master pop key
                        master_pop_key = struct.unpack(
                            "<I", transceiver.read_memory(
                                placement.x, placement.y, reading_address,
                                self._BYTES_PER_WORD))[0]
                        reading_address += self._BYTES_PER_WORD

                        # how many words the bitfield uses
                        n_words_to_read = struct.unpack(
                            "<I", transceiver.read_memory(
                                placement.x, placement.y, reading_address,
                                self._BYTES_PER_WORD))[0]
                        reading_address += self._BYTES_PER_WORD

                        # get bitfield words
                        bit_field = struct.unpack(
                            "<{}I".format(n_words_to_read),
                            transceiver.read_memory(
                                placement.x, placement.y, reading_address,
                                n_words_to_read *
                                constants.WORD_TO_BYTE_MULTIPLIER))
                        reading_address += (
                            n_words_to_read * constants.WORD_TO_BYTE_MULTIPLIER)

                        # put into report
                        n_neurons = n_words_to_read * self._BITS_IN_A_WORD
                        for neuron_id in range(0, n_neurons):
                            output.write(
                                "for key {} neuron id {} has bit {} "
                                "set \n".format(
                                    master_pop_key, neuron_id,
                                    self._bit_for_neuron_id(
                                        bit_field, neuron_id)))

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
            self, app_graph, graph_mapper, transceiver, placements, machine,
            progress, executable_finder, machine_graph, routing_infos):
        """ gets the data needed for the bit field expander for the machine

        :param app_graph: app graph
        :param graph_mapper: graph mapper between app graph and machine graph
        :param transceiver: SpiNNMan instance
        :param placements: placements
        :param machine: SpiNNMachine instance
        :param progress: progress bar
        :param executable_finder: where to find the executable
        :param machine_graph: the machine graph
        :param routing_infos: the key to edge map
        :return: data and expander cores
        """

        # storage for the data addresses needed for the bitfield
        data_address = dict()

        # cores to place bitfield expander
        expander_cores = ExecutableTargets()

        # bit field expander executable file path
        bit_field_expander_path = executable_finder.get_executable_path(
            self._BIT_FIELD_EXPANDER_APLX)

        # locate verts which can have a synaptic matrix to begin with
        for app_vertex in progress.over(app_graph.vertices, False):
            if isinstance(app_vertex, AbstractUsesPopulationTableAndSynapses):
                machine_verts = graph_mapper.get_machine_vertices(app_vertex)
                for machine_vertex in machine_verts:
                    placement = \
                        placements.get_placement_of_vertex(machine_vertex)

                    # check if the chip being considered already.
                    if (placement.x, placement.y) not in data_address:
                        data_address[(placement.x, placement.y)] = dict()
                        expander_cores.add_processor(
                            bit_field_expander_path, placement.x, placement.y,
                            machine.get_chip_at(placement.x, placement.y).
                            get_first_none_monitor_processor().processor_id)

                    # find the max atoms from source from each edge
                    edge_key_to_max_atom_map = \
                        self._get_edge_to_max_atoms_map(
                            machine_vertex, machine_graph, routing_infos,
                            graph_mapper)

                    # add the extra data
                    data_address[(placement.x, placement.y)][placement.p] = (
                        (app_vertex.master_pop_table_base_address(
                            transceiver, placement),
                         app_vertex.synaptic_matrix_base_address(
                             transceiver, placement),
                         app_vertex.bit_field_base_address(
                             transceiver, placement),
                         app_vertex.direct_matrix_base_address(
                            transceiver, placement),
                         edge_key_to_max_atom_map))

        return data_address, expander_cores

    @staticmethod
    def _get_edge_to_max_atoms_map(
            machine_vertex, machine_graph, routing_infos, graph_mapper):
        """ generates the map between key and n_atoms
        
        :param machine_vertex: the machine vertex which is the destination of\
         the edges to be considered
        :param machine_graph: the machine graph
        :param routing_infos: the key to edge map
        :param graph_mapper: mapping between app and machine vertex
        :return: dict of key to max_atoms
        """
        keys_to_max_atoms_map = dict()
        in_coming_edges = \
            machine_graph.get_edges_ending_at_vertex(machine_vertex)
        for in_coming_edge in in_coming_edges:
            key = routing_infos.get_first_key_from_partition(
                machine_graph.get_outgoing_partition_for_edge(in_coming_edge))
            keys_to_max_atoms_map[key] = (
                graph_mapper.get_slice(in_coming_edge.pre_vertex).n_atoms)
        return keys_to_max_atoms_map

    def _allocate_sdram_and_fill_in(self, data_address, transceiver):
        """ loads the app data for the bitfield generation

        :param data_address: the data base addresses for the cores in question
        :param transceiver: SpiNNMan instance
        :return: the bitfield app id
        """

        # new app id for the bitfield expander
        bit_field_generator_app_id = transceiver.app_id_tracker.get_new_id()

        # for each chip, allocate and fill in bitfield generated data.
        for (chip_x, chip_y) in data_address.keys():
            sdram_required = 0

            # chip level regions
            regions = data_address[(chip_x, chip_y)]

            # get each processor addresses and key to n_atoms map
            for processor in data_address[(chip_x, chip_y)].keys():
                sdram_required += (
                    (self._N_REGION_DATA_SETS_IN_WORDS +
                     self._N_ELEMENTS_PER_REGION_ELEMENT) *
                    constants.WORD_TO_BYTE_MULTIPLIER)
                (_, _, _, _, key_to_n_atoms) = \
                    data_address[(chip_x, chip_y)][processor]
                sdram_required += (
                    (self._N_KEYS_DATA_SET_IN_WORDS + (
                        len(key_to_n_atoms.keys()) *
                        self._N_ELEMENTS_IN_EACH_KEY_N_ATOM_MAP) *
                     constants.WORD_TO_BYTE_MULTIPLIER))

            # allocate sdram on chip for data size
            base_address = transceiver.malloc_sdram(
                chip_x, chip_y, sdram_required, bit_field_generator_app_id,
                self._SDRAM_TAG)
            transceiver.write_memory(
                chip_x, chip_y, base_address, self._generate_data(regions))
        return bit_field_generator_app_id

    def _generate_data(self, regions):
        """ generates the chips worth of data for regions to bitfield

        :param regions: list of tuples of master pop, synaptic matrix
        :return: data in byte array format for a given chip's bit field \
                 generator
        """
        data = b''

        key_to_atom_regions = list()

        # x bitfields
        data += self._ONE_WORDS.pack(len(regions))

        # load each regions data for bitfield
        for processor_id in regions.keys():
            (master_pop_base_address, synaptic_matrix_base_address,
             bit_field_base_address, direct_matrix_base_address,
             key_to_n_atoms) = regions[processor_id]

            # write the region base address's
            data += self._FOUR_WORDS.pack(
                master_pop_base_address, synaptic_matrix_base_address,
                bit_field_base_address, direct_matrix_base_address)

            # store for bottom store
            key_to_atom_regions.append(key_to_n_atoms)

        # plonk these at the bottom to ensure we can get them during the
        # process without dtcm issues.
        for key_to_n_atoms in key_to_atom_regions:
            data += self._ONE_WORDS.pack(len(key_to_n_atoms))
            # write the key to n atom maps
            for routing_key in key_to_n_atoms:
                data += self._TWO_WORDS.pack(
                    int(routing_key), int(key_to_n_atoms[routing_key]))
        return bytearray(data)

    def _run_app(
            self, executable_cores, bit_field_app_id, transceiver,
            provenance_file_path, executable_finder,
            read_bit_field_generator_iobuf):
        """ executes the app

        :param executable_cores: the cores to run the bit field expander on
        :param bit_field_app_id: the appid for the bit field expander
        :param transceiver: the SpiNNMan instance
        :param provenance_file_path: the path for where provenance data is\
        stored
        :param read_bit_field_generator_iobuf: bool flag for report
        :param executable_finder: finder for executable paths
        :rtype: None
        """

        # load the bitfield expander executable
        transceiver.execute_application(executable_cores, bit_field_app_id)

        # Wait for the executable to finish
        succeeded = False
        try:
            transceiver.wait_for_cores_to_be_in_state(
                executable_cores.all_core_subsets, bit_field_app_id,
                [CPUState.FINISHED])
            succeeded = True
        finally:
            # get the debug data
            if not succeeded:
                self._handle_failure(
                    executable_cores, transceiver, provenance_file_path,
                    bit_field_app_id, executable_finder)

        # Check if any cores have not completed successfully
        self._check_for_success(
            executable_cores, transceiver, provenance_file_path,
            bit_field_app_id, executable_finder)

        # if doing iobuf, read iobuf
        if read_bit_field_generator_iobuf:
            iobuf_reader = ChipIOBufExtractor()
            iobuf_reader(
                transceiver, executable_cores, executable_finder,
                provenance_file_path)

        # stop anything that's associated with the compressor binary
        transceiver.stop_application(bit_field_app_id)
        transceiver.app_id_tracker.free_id(bit_field_app_id)

    def _check_for_success(
            self, executable_targets, transceiver, provenance_file_path,
            compressor_app_id, executable_finder):
        """ Goes through the cores checking for cores that have failed to\
            expand the bitfield to the core

        :param executable_targets: cores to load bitfield on
        :param transceiver: SpiNNMan instance
        :param provenance_file_path: path to provenance folder
        :param compressor_app_id: the app id for the compressor c code
        :param executable_finder: exeuctable path finder
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

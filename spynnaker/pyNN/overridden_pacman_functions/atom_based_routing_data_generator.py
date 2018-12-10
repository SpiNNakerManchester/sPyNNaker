from spinn_utilities.progress_bar import ProgressBar
from spinnman.model import ExecutableTargets
from spinnman.model.enums import CPUState
from spynnaker.pyNN.models.abstract_models import \
    AbstractAcceptsIncomingSynapses
import struct


class SpynnakerAtomBasedRoutingDataGenerator(object):
    """ Executes bitfield and routing table entries for atom based routing
    """

    __slots__ = ()

    _SDRAM_TAG = 2
    _N_BYTES_PER_REGION_ELEMENT = 8
    _ONE_WORDS = struct.Struct("<I")
    _TWO_WORDS = struct.Struct("<II")
    _BIT_FIELD_EXPANDER_APLX = "synapse_expander.aplx"

    def __call__(
            self, placements, app_graph, executable_finder,
            provenance_file_path, machine, transceiver, graph_mapper):

        # pylint: disable=too-many-arguments

        # progress bar
        progress = ProgressBar(
            len(app_graph.vertices) + 2,
            "Running bitfield generation on chip")

        # get data
        data_address, expander_cores = self._calculate_core_data(
            app_graph, graph_mapper, transceiver, placements, machine,
            progress, executable_finder)

        # load data
        bit_field_app_id = self._allocate_sdram_and_fill_in(
            data_address, transceiver)
        progress.update(1)

        # run app
        self._run_app(
            expander_cores, bit_field_app_id, transceiver, provenance_file_path)

        progress.end()

    def _calculate_core_data(
            self, app_graph, graph_mapper, transceiver, placements, machine,
            progress, executable_finder):
        """ gets the data needed for the bit field expander for the machine
        
        :param app_graph: app graph
        :param graph_mapper: graph mapper between app graph and machine graph
        :param transceiver: spinnman instance
        :param placements: placements
        :param machine: spinnMachine instance
        :param progress: progress bar
        :param executable_finder: where to find the executable
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
            if isinstance(app_vertex, AbstractAcceptsIncomingSynapses):
                machine_verts = graph_mapper.get_machine_vertices(app_vertex)
                for machine_vertex in machine_verts:
                    # locate the 2 data region base addresses
                    placement = \
                        placements.get_placement_of_vertex(machine_vertex)
                    synaptic_matrix_base_address = \
                        machine_vertex.synaptic_matrix_base_address(
                            transceiver, placement)
                    master_pop_table_base_address = \
                        machine_vertex.master_pop_table_base_address(
                            transceiver, placement)

                    # check if the chip being considered already.
                    if (placement.x, placement.y) not in data_address:
                        data_address[(placement.x, placement.y)] = list()
                        expander_cores.add_processor(
                            bit_field_expander_path, placement.x, placement.y,
                            machine.get_chip_at(
                                placement.x,
                                placement.y).get_first_none_monitor_processor())

                    # add the extra data
                    data_address[(placement.x, placement.y)].append(
                        (master_pop_table_base_address,
                         synaptic_matrix_base_address))

        return data_address, expander_cores

    def _allocate_sdram_and_fill_in(self, data_address, transceiver):
        """ loads the app data for the bitfield generation
        
        :param data_address: the data base addresses for the cores in question
        :param transceiver: spinnman
        :return: the bitfield app id 
        """

        # new app id for the bitfield expander
        bit_field_generator_app_id = transceiver.app_id_tracker.get_new_id()
        for (chip_x, chip_y) in data_address.keys():
            regions = data_address[(chip_x, chip_y)]
            base_address = transceiver.malloc_sdram(
                chip_x, chip_y, len(regions) * self._N_BYTES_PER_REGION_ELEMENT,
                bit_field_generator_app_id, self._SDRAM_TAG)
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
        data += self._ONE_WORDS.pack(len(regions))
        for (master_pop_base_address, synaptic_matrix_base_address) in regions:
            data += self._TWO_WORDS.pack(master_pop_base_address,
                                         synaptic_matrix_base_address)
        return bytearray(data)

    def _run_app(
            self, executable_cores, bit_field_app_id, transceiver,
            provenance_file_path):

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
                    bit_field_app_id)

        # Check if any cores have not completed successfully
        self._check_for_success(
            executable_cores, transceiver,
            provenance_file_path, bit_field_app_id)

        # stop anything that's associated with the compressor binary
        transceiver.stop_application(bit_field_app_id)
        transceiver.app_id_tracker.free_id(bit_field_app_id)


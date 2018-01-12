from spinn_front_end_common.utilities import exceptions
from spinnman.model.enums.cpu_state import CPUState
import sys
from spinn_front_end_common.interface.interface_functions. \
    chip_iobuf_extractor import ChipIOBufExtractor
from spinnman.model.executable_targets import \
    ExecutableTargets

from spinn_machine.core_subsets import CoreSubsets
from spinn_utilities.progress_bar import ProgressBar

import logging
import os
import struct

import numpy
from spynnaker.pyNN.models.neural_projections.projection_application_edge \
    import ProjectionApplicationEdge

from spynnaker.pyNN.models.neuron.abstract_population_vertex \
    import AbstractPopulationVertex
# just to get app dir!
from spinn_front_end_common.connection_builder import connection_builder_app

logger = logging.getLogger(__name__)

# The SDRAM Tag used by the application - note this is fixed in the APLX
CONN_SDRAM_TAG = 140  # whaaat!?!?!? should this be defined in another file???
DLY_SDRAM_TAG = 160  # whaaat!?!?!? should this be defined in another file???

MAX_32 = numpy.uint32(0xFFFFFFFF)

FORCE_EXTRACT = True if 0 else False

class ConnectionBuilder(object):
    """ Compressor that uses a on chip router compressor
    """

    def __call__(
            self, placements, graph_mapper, application_graph, machine_graph, \
            routing_infos, dsg_targets, loaded_application_data_token, \
            transceiver, machine, app_id, provenance_file_path, \
            binaries_path="./"):
        """
        :param transceiver: the spinnman interface
        :param machine: the spinnaker machine representation
        :param app_id: the app-id used by the main application
        :param provenance_file_path: the path to where to write the data
        :return: flag stating routing compression and loading has been done
        """
        if not loaded_application_data_token:
            raise exceptions.ConfigurationException(
                    "The token for having loaded the application data token is set"
                    " to false and therefore I cannot run. Please fix and try "
                    "again")
        # build progress bar
        progress_bar = ProgressBar(machine_graph.n_vertices + 2,
                                   "Running build connectors on chip")


        def place2txt(placement):
            return "%d_%d_%d"%(placement.x, placement.y, placement.p)

        delayed = False
        conn_ran_on_core = {}
        delay_ran_on_core = {}
        some_delayed = False
        delay_base_address = 0
        delayed_placements = {}
        builder_placements = {}
        conn_builder_app_id = transceiver.app_id_tracker.get_new_id()
        delay_recv_app_id = transceiver.app_id_tracker.get_new_id()
        any_built_on_machine = False
        placement = None
        delayed_places = []
        for machine_vertex in machine_graph.vertices:
            delayed = False
            app_vertex = graph_mapper.get_application_vertex(machine_vertex)
            if isinstance(app_vertex, AbstractPopulationVertex):


                in_edges = machine_graph.get_edges_ending_at_vertex(machine_vertex)
                flags, num_edges = self._generate_on_machine_flags(in_edges, graph_mapper)

                num_on_machine = numpy.sum([bin(f).count("1") for f in flags])

                if num_on_machine == 0:
                    progress_bar.update()
                    continue

                any_built_on_machine = True

                all_on_machine = (num_edges == num_on_machine)

                # print("In ConnectionBuilder: ")
                # print("\tpopulation = %s" % app_vertex.label)
                # print("\tNum of on machine generation = %d" % num_on_machine)

                post_slice = graph_mapper.get_slice(machine_vertex)
                post_slice_start = numpy.uint32(post_slice.lo_atom)
                post_slice_count = numpy.uint32(post_slice.n_atoms)

                placement = placements.get_placement_of_vertex(machine_vertex)
                if not (place2txt(placement) in builder_placements.keys()):
                    builder_placements[place2txt(placement)] = placement

                # print("This app placement")
                # print(placement)

                delayed_places[:] = self._get_placements_for_delayed(
                                    in_edges, graph_mapper, placements)
                for plc in delayed_places:
                    if not (place2txt(plc) in delayed_placements.keys()):
                        delayed_placements[place2txt(plc)] = plc

                if delayed_places:
                    some_delayed = True
                    for plc in delayed_places:

                        # print("has delayed run on %s?"%self._place2str(plc))
                        if self._place2str(plc) not in delay_ran_on_core and all_on_machine:
                            first_run_dly = int(0x55555555)
                            delay_ran_on_core[self._place2str(plc)] = True
                            # go to spinnman and ask for a memory region of that size per chip.
                            delay_base_address = transceiver.malloc_sdram(
                                plc.x, plc.y, 4, delay_recv_app_id,
                                DLY_SDRAM_TAG + plc.p)

                            self._place2str(plc)
                            # print("\tNo")
                        else:
                            # print("\tYes")
                            first_run_dly = int(0)


                        # print("delayed base address 0x%08x"%delay_base_address)
                        # write sdram requirements per chip
                        transceiver.write_memory(
                            plc.x, plc.y, delay_base_address, first_run_dly)




                # print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                # print("has connection builder run in %s?" %
                #       self._place2str(placement))
                base_address = transceiver.malloc_sdram(placement.x, placement.y, 4,
                                                        conn_builder_app_id,
                                                        CONN_SDRAM_TAG + placement.p)
                if not (self._place2str(placement) in conn_ran_on_core.keys()) and \
                        all_on_machine:
                    first_run_conn = int(0x55555555)
                    conn_ran_on_core[self._place2str(placement)] = True

                    # print("\tNo")
                else:
                    # print("\tYes")
                    first_run_conn = int(0)
                # go to spinnman and ask for a memory region of that size per chip.
                # print("conn_bldr 0x%08x"%base_address)
                # write sdram requirements per chip
                # print(first_run_conn)
                transceiver.write_memory(placement.x, placement.y,
                                         base_address, first_run_conn)

                progress_bar.update()

        progress_bar.update()

        if any_built_on_machine:
            # print("\tLoading delay extension receiver at:")
            # print(delayed_placements)
            delay_recv_tgt = self._load_executables(delayed_placements.values(),
                                                    delay_recv_app_id,
                                                    transceiver, machine,
                                                    "delay_extension_receiver.aplx")

            if FORCE_EXTRACT:
                print("Loading executables")
            # Wait for delay receivers to be in wait state
            try:
                transceiver.wait_for_cores_to_be_in_state(
                        delay_recv_tgt.all_core_subsets, delay_recv_app_id,
                        [CPUState.RUNNING])  # SYNC0, SYNC1, CPU_STATE_12,13,14
            except:
                # get the debug data
                self._handle_failure(delay_recv_tgt, transceiver,
                                     provenance_file_path, delay_recv_app_id,
                                     'DelayReceiver-Load')

                exc_type, exc_value, exc_traceback = sys.exc_info()
                raise exc_type, exc_value, exc_traceback

            # print("\n\tLoading Connection Builder at:")
            # print(builder_placements)

            conn_bldr_tgt = self._load_executables(builder_placements.values(),
                                                   conn_builder_app_id,
                                                   transceiver, machine,
                                                   "connection_builder.aplx")

            # time.sleep(0.1*len(builder_placements))
            if FORCE_EXTRACT:
                print("\n... Waiting for conn builder to stop\n")
            # Wait for delay receivers to be in wait state
            try:
                transceiver.wait_for_cores_to_be_in_state(
                        conn_bldr_tgt.all_core_subsets, conn_builder_app_id,
                        # [CPUState.PAUSED])
                        [CPUState.FINISHED],
                        )
                        # timeout=2 * 60.)
                # FINISHED, SYNC0, SYNC1, CPU_STATE_12,13,14
            except:

                # get the debug data
                self._handle_failure(conn_bldr_tgt, transceiver, provenance_file_path,
                                     conn_builder_app_id, 'ConnectionBuilder')

                if delayed_placements:
                    self._handle_failure(delay_recv_tgt, transceiver,
                                         provenance_file_path,
                                         delay_recv_app_id, 'DelayReceiver')

                exc_type, exc_value, exc_traceback = sys.exc_info()
                raise exc_type, exc_value, exc_traceback


            if FORCE_EXTRACT:
                print("Extracting ConnectionBuilder IO buffer for core")
                self._extract_iobuf(conn_bldr_tgt, transceiver, provenance_file_path,
                                    'connection_builder_enforced')

            transceiver.stop_application(conn_builder_app_id)

            if delayed_placements:
                if FORCE_EXTRACT:
                    print("Extracting DelayExtensionReceiver IO buffer for core")
                    self._extract_iobuf(delay_recv_tgt, transceiver,
                                        provenance_file_path,
                                        'delay_receiver_enforced')
                transceiver.stop_application(delay_recv_app_id)

            transceiver.app_id_tracker.free_id(conn_builder_app_id)

            if some_delayed:
                transceiver.app_id_tracker.free_id(delay_recv_app_id)


        #free all connection builder memory (MemoryRegions)
        progress_bar.update()

        progress_bar.end()

        # return generate on machine flag
        return True


    def _check_for_success(
            self, executable_targets, transceiver, provenance_file_path,
            app_id):
        """ goes through the cores checking for cores that have failed to\
            compress the routing tables to the level where they fit into the\
            router
        """
        # print("SKIPPED check for success :O !!!")
        for core_subset in executable_targets.all_core_subsets:
            x = core_subset.x
            y = core_subset.y
            for p in core_subset.processor_ids:

                # Read the result from USER0 register
                user_0_address = \
                    transceiver.get_user_0_register_address_from_core(x, y, p)

                result = struct.unpack(
                      "<I", str(transceiver.read_memory(x, y, user_0_address, 4)))[0]

                # The result is 0 if success, otherwise failure
                if result != 0:
                    self._handle_failure(
                            executable_targets, transceiver, provenance_file_path,
                            app_id)

                    raise exceptions.SpinnFrontEndException(
                            "On Machine Connection Builder on {}, {} failed to complete"
                                .format(x, y))


    def _extract_iobuf(self, executable_targets, transceiver, provenance_file_path,
                       fname='connection_builder'):
        iobuf_extractor = ChipIOBufExtractor()
        io_errors, io_warnings = iobuf_extractor(
                transceiver, True, executable_targets.all_core_subsets, provenance_file_path)
        # self._write_iobuf(io_buffers, provenance_file_path, fname)
        for warning in io_warnings:
            logger.warn(warning)
        for error in io_errors:
            logger.error(error)


    def _handle_failure(
            self, executable_targets, transceiver, provenance_file_path,
            app_id, module="Builder"):
        """

        :param executable_targets:
        :param transceiver:
        :param provenance_file_path:
        :param prov_items:
        :return:
        """
        logger.info("On Machine Connection Builder has failed --- %s"%module)

        self._extract_iobuf(executable_targets, transceiver,
                            provenance_file_path, module)

        transceiver.stop_application(app_id)
        transceiver.app_id_tracker.free_id(app_id)

    @staticmethod
    def _write_iobuf(io_buffers, provenance_file_path, fname='connection_builder'):
        """ writes the iobuf to files

        :param io_buffers: the iobuf for the cores
        :param provenance_file_path:\
            the file path where the iobuf are to be stored
        :return: None
        """
        for iobuf in io_buffers:
            file_name = os.path.join(
                    provenance_file_path,
                    "{}_{}_{}_{}.txt".format(iobuf.x, iobuf.y, iobuf.p, fname))
            count = 2
            while os.path.exists(file_name):
                file_name = os.path.join(
                        provenance_file_path,
                        "{}_{}_{}_{}_{}.txt".format(
                                iobuf.x, iobuf.y, iobuf.p, fname, count))
                count += 1
            writer = open(file_name, "w+")
            writer.write(iobuf.iobuf)
            writer.close()

    def _free_sdram(self, placements, app_id, transciever):
        for placement in placements:
            transciever.free_sdram_by_app_id(placement.x, placement.y, app_id)

    def _load_executables(self, placements, app_id, transceiver, machine, binary_name):

        # build core subsets
        core_subsets = CoreSubsets()

        for placement in placements:
            # get the first none monitor core
            chip = machine.get_chip_at(placement.x, placement.y)
            # processor = chip.get_first_none_monitor_processor()

            # add to the core subsets
            # core_subsets.add_processor(placement.x, placement.y, processor.processor_id)
            core_subsets.add_processor(placement.x, placement.y, placement.p)

        # build binary path
        conn_bldr_app_dir = connection_builder_app.__file__
        binary_path = os.path.join(os.path.dirname(conn_bldr_app_dir), binary_name)

        # build executable targets
        executable_targets = ExecutableTargets()
        executable_targets.add_subsets(binary_path, core_subsets)

        transceiver.execute_application(executable_targets, app_id)

        return executable_targets


    # **TODO** move to a common file between synaptic_manager and this
    def _generate_on_machine_flags(self, in_edges, graph_mapper):
        syn_infos = []
        for edg in in_edges:
            app_edge = graph_mapper.get_application_edge(edg)
            if isinstance(app_edge, ProjectionApplicationEdge):
                for synapse_info in app_edge.synapse_information:
                    syn_infos.append(synapse_info)

        num_edges = len(syn_infos)
        num_words = int(numpy.ceil(num_edges / 32.))
        flags = numpy.zeros(num_words, dtype=numpy.uint32)
        e = 0
        # print("\nIn _generate_on_machine_flags ================")
        for syn_info in syn_infos:
            # syn_info = edg.synapse_information[0]
            conn = syn_info.connector
            # print("\t%s - %s"%(conn, conn.generate_on_machine()))
            word = e // 32
            shift = e % 32
            if conn.generate_on_machine():
                flags[word] |= 1 << shift
            e += 1

        return flags, num_edges


    def _get_placements_for_delayed(self, in_edges, graph_mapper, placements):
        places = []

        for edg in in_edges:
            app_edge = graph_mapper.get_application_edge(edg)
            # if isinstance(app_edge, ProjectionApplicationEdge):
            if hasattr(app_edge, 'delay_edge') and app_edge.delay_edge is not None:
                vertices = graph_mapper.get_machine_vertices(app_edge.delay_edge.pre_vertex)

                for machine_vertex in vertices:
                    place = placements.get_placement_of_vertex(machine_vertex)
                    if place not in places:
                        places.append(place)

        return places


    def _is_delayed(self, synapse_info):
        conn = synapse_info.connector
        return numpy.uint32(conn.get_delay_maximum() > 16)

        # **TODO** END --- move to common file

    def _place2str(self, placement):
        return "%d_%d_%d"%(placement.x, placement.y, placement.p)
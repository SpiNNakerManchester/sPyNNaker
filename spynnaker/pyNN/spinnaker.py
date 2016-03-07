
# pacman imports
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.operations.pacman_algorithm_executor import PACMANAlgorithmExecutor


# common front end imports
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.interface.buffer_management\
    .buffer_models.abstract_receive_buffers_to_host \
    import AbstractReceiveBuffersToHost
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.interface.executable_finder import ExecutableFinder

# local front end imports
from spynnaker.pyNN.models.common.abstract_gsyn_recordable\
    import AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable\
    import AbstractVRecordable
from spynnaker.pyNN.models.common.abstract_spike_recordable \
    import AbstractSpikeRecordable
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN import overridden_pacman_functions
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.models.abstract_models\
    .abstract_send_me_multicast_commands_vertex \
    import AbstractSendMeMulticastCommandsVertex
from spynnaker.pyNN.models.abstract_models\
    .abstract_vertex_with_dependent_vertices \
    import AbstractVertexWithEdgeToDependentVertices
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models\
    .abstract_has_first_machine_time_step \
    import AbstractHasFirstMachineTimeStep


# general imports
from collections import defaultdict
import logging
import math
import os

logger = logging.getLogger(__name__)

executable_finder = ExecutableFinder()


class Spinnaker(object):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None,
                 database_socket_addresses=None):

        self._hostname = host_name

        # update graph label if needed
        if graph_label is None:
            graph_label = "Application_graph"

        # delays parameters
        self._min_supported_delay = None
        self._max_supported_delay = None

        # pacman objects
        self._partitionable_graph = PartitionableGraph(label=graph_label)
        self._mapping_outputs = None
        self._load_outputs = None
        self._partitioned_graph = None
        self._graph_mapper = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._tags = None
        self._machine = None
        self._txrx = None
        self._buffer_manager = None

        # database objects
        self._database_socket_addresses = set()
        if database_socket_addresses is not None:
            self._database_socket_addresses.union(database_socket_addresses)

        # Determine default executable folder location
        # and add this default to end of list of search paths
        executable_finder.add_path(os.path.dirname(model_binaries.__file__))

        # population holders
        self._populations = list()
        self._projections = list()
        self._multi_cast_vertex = None
        self._edge_count = 0

        # holder for timing related values
        self._has_ran = False
        self._has_reset_last = False
        self._current_run_timesteps = 0
        self._no_machine_time_steps = None
        self._machine_time_step = None
        self._no_sync_changes = 0
        self._minimum_step_generated = None

        self._app_id = config.getint("Machine", "appID")

        # set up reports default folder
        self._report_default_directory, this_run_time_string = \
            helpful_functions.set_up_report_specifics(
                default_report_file_path=config.get(
                    "Reports", "defaultReportFilePath"),
                max_reports_kept=config.getint(
                    "Reports", "max_reports_kept"),
                app_id=self._app_id)

        # set up application report folder
        self._app_data_runtime_folder = \
            helpful_functions.set_up_output_application_data_specifics(
                max_application_binaries_kept=config.getint(
                    "Reports", "max_application_binaries_kept"),
                where_to_write_application_data_files=config.get(
                    "Reports", "defaultApplicationDataFilePath"),
                app_id=self._app_id,
                this_run_time_string=this_run_time_string)

        # make a folder for the json files to be stored in
        self._json_folder = os.path.join(
            self._report_default_directory, "json_files")
        if not os.path.exists(self._json_folder):
            os.makedirs(self._json_folder)
        self._provenance_file_path = os.path.join(
            self._report_default_directory, "provenance_data")
        if not os.path.exists(self._provenance_file_path):
            os.makedirs(self._provenance_file_path)

        self._xml_paths = self._create_xml_paths()
        self._do_timings = config.getboolean(
            "Reports", "outputTimesForSections")
        self._exec_dse_on_host = config.getboolean(
            "SpecExecution", "specExecOnHost")

        # set up machine targeted data
        self._set_up_machine_specifics(
            timestep, min_delay, max_delay, host_name)

        logger.info("Setting time scale factor to {}.".format(
            self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds.".format(
            self._machine_time_step))

    def _set_up_machine_specifics(self, timestep, min_delay, max_delay,
                                  hostname):
        self._machine_time_step = config.getint("Machine", "machineTimeStep")

        # deal with params allowed via the setup options
        if timestep is not None:

            # convert into milliseconds from microseconds
            timestep *= 1000
            self._machine_time_step = timestep

        if min_delay is not None and float(min_delay * 1000) < 1.0 * timestep:
            raise common_exceptions.ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step"
                .format(constants.MIN_SUPPORTED_DELAY * timestep))

        natively_supported_delay_for_models = \
            constants.MAX_SUPPORTED_DELAY_TICS
        delay_extention_max_supported_delay = \
            constants.MAX_DELAY_BLOCKS \
            * constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extention_max_supported_delay

        if max_delay is not None\
           and float(max_delay * 1000) > max_delay_tics_supported * timestep:
            raise common_exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(0.144 * timestep))
        if min_delay is not None:
            self._min_supported_delay = min_delay
        else:
            self._min_supported_delay = timestep / 1000.0

        if max_delay is not None:
            self._max_supported_delay = max_delay
        else:
            self._max_supported_delay = (max_delay_tics_supported *
                                         (timestep / 1000.0))

        if (config.has_option("Machine", "timeScaleFactor") and
                config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = \
                config.getint("Machine", "timeScaleFactor")
            if timestep * self._time_scale_factor < 1000:
                logger.warn("the combination of machine time step and the "
                            "machine time scale factor results in a real "
                            "timer tick that is currently not reliably "
                            "supported by the spinnaker machine.")
        else:
            self._time_scale_factor = max(1,
                                          math.ceil(1000.0 / float(timestep)))
            if self._time_scale_factor > 1:
                logger.warn("A timestep was entered that has forced pacman103 "
                            "to automatically slow the simulation down from "
                            "real time by a factor of {}. To remove this "
                            "automatic behaviour, please enter a "
                            "timescaleFactor value in your .pacman.cfg"
                            .format(self._time_scale_factor))

        if hostname is not None:
            self._hostname = hostname
            logger.warn("The machine name from PYNN setup is overriding the "
                        "machine name defined in the spynnaker.cfg file")
        elif config.has_option("Machine", "machineName"):
            self._hostname = config.get("Machine", "machineName")
        else:
            raise Exception("A SpiNNaker machine must be specified in "
                            "spynnaker.cfg.")
        use_virtual_board = config.getboolean("Machine", "virtual_board")
        if self._hostname == 'None' and not use_virtual_board:
            raise Exception("A SpiNNaker machine must be specified in "
                            "spynnaker.cfg.")

    def run(self, run_time):

        n_machine_time_steps = None
        if run_time is not None:
            n_machine_time_steps = int(
                (run_time * 1000.0) / self._machine_time_step)

        # If we have never run before, or the graph has changed,
        # start by performing mapping
        application_graph_changed = self._detect_if_graph_has_changed(True)
        if not self._has_ran or application_graph_changed:
            if (application_graph_changed and self._has_ran and
                    not self._has_reset_last):
                raise NotImplementedError(
                    "The network cannot be changed between runs without"
                    " resetting")
            self._do_mapping(run_time, n_machine_time_steps)

        # Work out an array of timesteps to perform
        steps = None
        if not config.getboolean("Buffers", "use_auto_pause_and_resume"):

            # If reset without application graph change, the run time must be
            # the same as the first run time
            if (self._has_reset_last and
                    self._minimum_step_generated != n_machine_time_steps):
                raise common_exceptions.ConfigurationException(
                    "The run time after a reset must be the same as the first"
                    "run time")

            # Not currently possible to run the second time for more than the
            # first time without auto pause and resume
            if (self._minimum_step_generated is not None and
                    self._minimum_step_generated < n_machine_time_steps):
                raise common_exceptions.ConfigurationException(
                    "Second and subsequent run time must be less than or equal"
                    " to the first run time")

            steps = [n_machine_time_steps]
            self._minimum_step_generated = steps[0]
        else:

            # With auto pause and resume, any time step is possible but run
            # time more than the first will guarantee that run will be called
            # more than once
            if self._minimum_step_generated is not None:
                steps = self._generate_steps(
                    n_machine_time_steps, self._minimum_step_generated)
            else:
                steps = self._deduce_number_of_iterations(n_machine_time_steps)
                self._minimum_step_generated = steps[0]

        # If we have never run before, or the graph has changed, or a reset
        # has been requested, load the data
        if (not self._has_ran or application_graph_changed or
                self._has_reset_last):

            # Data generation needs to be done if not already done
            if application_graph_changed:
                self._do_data_generation(steps[0])
            self._do_load()

        # Run for each of the given steps
        for step in steps:
            self._do_run(step)

    def _deduce_number_of_iterations(self, n_machine_time_steps):

        # Go through the placements and find how much SDRAM is available
        # on each chip
        sdram_tracker = dict()
        vertex_by_chip = defaultdict(list)
        for placement in self._placements.placements:
            vertex = placement.subvertex
            if isinstance(vertex, AbstractReceiveBuffersToHost):
                resources = vertex.resources_required
                if (placement.x, placement.y) not in sdram_tracker:
                    sdram_tracker[placement.x, placement.y] = \
                        self._machine.get_chip_at(
                            placement.x, placement.y).sdram.size
                sdram = (
                    resources.sdram.get_value() -
                    vertex.get_minimum_buffer_sdram_usage())
                sdram_tracker[placement.x, placement.y] -= sdram
                vertex_by_chip[placement.x, placement.y].append(vertex)

        # Go through the chips and divide up the remaining SDRAM, finding
        # the minimum number of machine timesteps to assign
        min_time_steps = None
        for x, y in vertex_by_chip:
            vertices_on_chip = vertex_by_chip[x, y]
            sdram = sdram_tracker[x, y]
            sdram_per_vertex = int(sdram / len(vertices_on_chip))
            for vertex in vertices_on_chip:
                n_time_steps = vertex.get_n_timesteps_in_buffer_space(
                    sdram_per_vertex)
                if min_time_steps is None or n_time_steps < min_time_steps:
                    min_time_steps = n_time_steps

        return self._generate_steps(n_machine_time_steps, min_time_steps)

    @staticmethod
    def _generate_steps(n_machine_time_steps, min_machine_time_steps):
        number_of_full_iterations = int(math.floor(
            n_machine_time_steps / min_machine_time_steps))
        left_over_time_steps = int(
            n_machine_time_steps -
            (number_of_full_iterations * min_machine_time_steps))

        steps = [int(min_machine_time_steps)] * number_of_full_iterations
        if left_over_time_steps != 0:
            steps.append(int(left_over_time_steps))
        return steps

    def _update_n_machine_time_steps(self, n_machine_time_steps):
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractDataSpecableVertex):
                vertex.set_no_machine_time_steps(n_machine_time_steps)

    def _read_config(self, section, item):
        value = config.get(section, item)
        if value == "None":
            return None
        return value

    def _read_config_int(self, section, item):
        value = self._read_config(section, item)
        if value is None:
            return value
        return int(value)

    def _do_mapping(self, run_time, n_machine_time_steps):

        # Set the initial n_machine_time_steps to all of them for mapping
        # (note that the underlying vertices will know about
        # auto-pause-and-resume and so they will work correctly here regardless
        # of the setting)
        self._update_n_machine_time_steps(n_machine_time_steps)

        inputs = dict()
        inputs["RunTime"] = run_time
        inputs["MemoryPartitionableGraph"] = self._partitionable_graph
        inputs['ReportFolder'] = self._report_default_directory
        inputs["ApplicationDataFolder"] = self._app_data_runtime_folder
        inputs['IPAddress'] = self._hostname
        inputs["BMPDetails"] = config.get("Machine", "bmp_names")
        inputs["DownedChipsDetails"] = config.get("Machine", "down_chips")
        inputs["DownedCoresDetails"] = config.get("Machine", "down_cores")
        inputs["BoardVersion"] = config.getint("Machine", "version")
        inputs["NumberOfBoards"] = self._read_config_int(
            "Machine", "number_of_boards")
        inputs["MachineWidth"] = self._read_config_int("Machine", "width")
        inputs["MachineHeight"] = self._read_config_int("Machine", "height")
        inputs["AutoDetectBMPFlag"] = config.getboolean(
            "Machine", "auto_detect_bmp")
        inputs["EnableReinjectionFlag"] = config.getboolean(
            "Machine", "enable_reinjection")
        inputs["ScampConnectionData"] = self._read_config(
            "Machine", "scamp_connections_data")
        inputs["BootPortNum"] = self._read_config_int(
            "Machine", "boot_connection_port_num")
        inputs["APPID"] = self._app_id
        inputs["DSEAPPID"] = config.getint("Machine", "DSEappID")
        inputs["TimeScaleFactor"] = self._time_scale_factor
        inputs["MachineTimeStep"] = self._machine_time_step
        inputs["DatabaseSocketAddresses"] = self._database_socket_addresses
        inputs["DatabaseWaitOnConfirmationFlag"] = config.getboolean(
            "Database", "wait_on_confirmation")
        inputs["WriteCheckerFlag"] = config.getboolean(
            "Mode", "verify_writes")
        inputs["WriteTextSpecsFlag"] = config.getboolean(
            "Reports", "writeTextSpecs")
        inputs["ExecutableFinder"] = executable_finder
        inputs["MachineHasWrapAroundsFlag"] = config.getboolean(
            "Machine", "requires_wrap_arounds")
        inputs["UserCreateDatabaseFlag"] = config.get(
            "Database", "create_database")
        inputs["ExecuteMapping"] = config.getboolean(
            "Database", "create_routing_info_to_neuron_id_mapping")
        inputs["SendStartNotifications"] = config.getboolean(
            "Database", "send_start_notification")
        inputs["ResetMachineOnStartupFlag"] = config.getboolean(
            "Machine", "reset_machine_on_startup")
        inputs["MaxSDRAMSize"] = self._read_config_int(
            "Machine", "max_sdram_allowed_per_chip")

        # add paths for each file based version
        inputs["FileCoreAllocationsFilePath"] = os.path.join(
            self._json_folder, "core_allocations.json")
        inputs["FileSDRAMAllocationsFilePath"] = os.path.join(
            self._json_folder, "sdram_allocations.json")
        inputs["FileMachineFilePath"] = os.path.join(
            self._json_folder, "machine.json")
        inputs["FilePartitionedGraphFilePath"] = os.path.join(
            self._json_folder, "partitioned_graph.json")
        inputs["FilePlacementFilePath"] = os.path.join(
            self._json_folder, "placements.json")
        inputs["FileRouingPathsFilePath"] = os.path.join(
            self._json_folder, "routing_paths.json")
        inputs["FileConstraintsFilePath"] = os.path.join(
            self._json_folder, "constraints.json")

        algorithms = list()

        # handle virtual machine and its linking to multi-run
        if config.getboolean("Machine", "virtual_board"):
            algorithms.append("FrontEndCommonVirtualMachineInterfacer")
        else:
            if self._machine is None and self._txrx is None:
                algorithms.append("FrontEndCommonMachineInterfacer")
            else:
                inputs["MemoryMachine"] = self._machine
                inputs["MemoryTransceiver"] = self._txrx

        # always add extended machine builder
        algorithms.append("MallocBasedChipIDAllocator")

        # Add reports
        if config.getboolean("Reports", "reportsEnabled"):
            if config.getboolean("Reports", "writeTagAllocationReports"):
                algorithms.append("TagReport")
            if config.getboolean("Reports", "writeRouterInfoReport"):
                algorithms.append("routingInfoReports")
            if config.getboolean("Reports", "writeRouterReports"):
                algorithms.append("RouterReports")
            if config.getboolean("Reports", "writeRoutingTableReports"):
                algorithms.append("unCompressedRoutingTableReports")
                algorithms.append("compressedRoutingTableReports")
                algorithms.append("comparisonOfRoutingTablesReport")
            if config.getboolean("Reports", "writePartitionerReports"):
                algorithms.append("PartitionerReport")
            if config.getboolean(
                    "Reports", "writePlacerReportWithPartitionable"):
                algorithms.append("PlacerReportWithPartitionableGraph")
            if config.getboolean(
                    "Reports", "writePlacerReportWithoutPartitionable"):
                algorithms.append("PlacerReportWithoutPartitionableGraph")
            if config.getboolean("Reports", "writeNetworkSpecificationReport"):
                algorithms.append(
                    "FrontEndCommonNetworkSpecificationPartitionableReport")

        algorithms.extend(config.get("Mapping", "algorithms").split(","))

        outputs = [
            "MemoryTransceiver", "MemoryPlacements", "MemoryRoutingTables",
            "MemoryTags", "MemoryGraphMapper", "MemoryPartitionedGraph",
            "MemoryMachine", "MemoryRoutingInfos"]

        # Execute the mapping algorithms
        executor = PACMANAlgorithmExecutor(
            algorithms, [], inputs, self._xml_paths, outputs, self._do_timings)
        executor.execute_mapping()
        self._mapping_outputs = executor.get_items()

        # Get the outputs needed
        if not config.getboolean("Machine", "virtual_board"):
            self._txrx = executor.get_item("MemoryTransceiver")
        self._placements = executor.get_item("MemoryPlacements")
        self._router_tables = executor.get_item("MemoryRoutingTables")
        self._tags = executor.get_item("MemoryTags")
        self._graph_mapper = executor.get_item("MemoryGraphMapper")
        self._partitioned_graph = executor.get_item("MemoryPartitionedGraph")
        self._machine = executor.get_item("MemoryMachine")
        self._routing_infos = executor.get_item("MemoryRoutingInfos")

    def _do_data_generation(self, n_machine_time_steps):

        # Update the machine timesteps again for the data generation
        self._update_n_machine_time_steps(n_machine_time_steps)

        # The initial inputs are the mapping outputs
        inputs = dict(self._mapping_outputs)

        # Run the data generation algorithms
        algorithms = [
            "FrontEndCommomPartitionableGraphDataSpecificationWriter"]

        executor = PACMANAlgorithmExecutor(
            algorithms, [], inputs, self._xml_paths, [], self._do_timings)
        executor.execute_mapping()
        self._mapping_outputs = executor.get_items()

    def _do_load(self):

        # The initial inputs are the mapping outputs
        inputs = dict(self._mapping_outputs)
        inputs["WriteReloadFilesFlag"] = (
            config.getboolean("Reports", "reportsEnabled") and
            config.getboolean("Reports", "writeReloadSteps")
        )
        inputs["WriteMemoryMapReportFlag"] = (
            config.getboolean("Reports", "reportsEnabled") and
            config.getboolean("Reports", "writeMemoryMapReport")
        )

        algorithms = list()
        optional_algorithms = list()
        optional_algorithms.append("FrontEndCommonRoutingTableLoader")
        optional_algorithms.append("FrontEndCommonTagsLoader")
        if self._exec_dse_on_host:
            optional_algorithms.append(
                "FrontEndCommonPartitionableGraphHostExecuteDataSpecification")
            if config.getboolean("Reports", "writeMemoryMapReport"):
                optional_algorithms.append(
                    "FrontEndCommonMemoryMapOnHostReport")
        else:
            optional_algorithms.append(
                "FrontEndCommonPartitionableGraphMachineExecuteDataSpecification")  # @IgnorePep8
            if config.getboolean("Reports", "writeMemoryMapReport"):
                optional_algorithms.append(
                    "FrontEndCommonMemoryMapOnChipReport")
        optional_algorithms.append("FrontEndCommonLoadExecutableImages")

        # always make the buffer manager
        algorithms.append("FrontEndCommonBufferManagerCreater")

        if (not self._has_ran and
                config.getboolean("Reports", "writeReloadSteps")):
            algorithms.append("FrontEndCommonReloadScriptCreator")
        elif (self.has_ran and
                config.getboolean("Reports", "writeReloadSteps")):
            logger.warn(
                "The reload script cannot handle multi-runs, nor can"
                "it handle resets, therefore it will only contain the "
                "initial run")

        outputs = [
            "LoadedReverseIPTagsToken", "LoadedIPTagsToken",
            "LoadedRoutingTablesToken", "LoadBinariesToken",
            "LoadedApplicationDataToken"
        ]

        executor = PACMANAlgorithmExecutor(
            algorithms, optional_algorithms, inputs, self._xml_paths,
            outputs, self._do_timings)
        executor.execute_mapping()
        self._load_outputs = executor.get_items()

    def _do_run(self, n_machine_time_steps):

        # calculate number of machine time steps
        total_run_timesteps = self._calculate_number_of_machine_time_steps(
            n_machine_time_steps)
        self._update_n_machine_time_steps(total_run_timesteps)
        run_time = (
            n_machine_time_steps * (float(self._machine_time_step) / 1000.0))

        # Calculate the first machine time step to start from and set this
        # where necessary
        first_machine_time_step = self._current_run_timesteps
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractHasFirstMachineTimeStep):
                vertex.set_first_machine_time_step(first_machine_time_step)

        inputs = dict(self._load_outputs)
        inputs["RanToken"] = self._has_ran
        inputs["NoSyncChanges"] = self._no_sync_changes
        inputs["ProvenanceFilePath"] = self._provenance_file_path
        inputs["RunTimeMachineTimeSteps"] = n_machine_time_steps
        inputs["RunTime"] = run_time

        algorithms = list()
        if self._has_ran and not self._has_reset_last:

            # add function for extracting all the recorded data from
            # recorded populations
            algorithms.append("SpyNNakerRecordingExtractor")

            algorithms.append("FrontEndCommonRuntimeUpdater")

        # Add the database writer in case it is needed
        algorithms.append("SpynnakerDatabaseWriter")
        algorithms.append("FrontEndCommonNotificationProtocol")
        algorithms.append("FrontEndCommonApplicationRunner")

        if (config.get("Reports", "reportsEnabled") and
                config.get("Reports", "writeProvenanceData") and
                not config.getboolean("Machine", "virtual_board")):
            algorithms.append("FrontEndCommonProvenanceGatherer")

        executor = PACMANAlgorithmExecutor(
            algorithms, [], inputs, self._xml_paths, [], self._do_timings)
        executor.execute_mapping()

        # gather provenance data from the executor itself if needed
        if (config.get("Reports", "writeProvenanceData") and
                not config.getboolean("Machine", "virtual_board")):
            pacman_executor_file_path = os.path.join(
                self._provenance_file_path, "PACMAN_provancence_data.xml")
            executor.write_provenance_data_in_xml(
                pacman_executor_file_path, self._txrx)

        self._current_run_timesteps = total_run_timesteps
        self._no_sync_changes = executor.get_item("NoSyncChanges")
        self._buffer_manager = executor.get_item("BufferManager")
        self._has_reset_last = False
        self._has_ran = True

    def reset(self):
        """ Code that puts the simulation back at time zero
        """

        logger.info("Starting reset progress")
        if self._txrx is not None:
            self._txrx.stop_application(self._app_id)

        # rewind the buffers from the buffer manager, to start at the beginning
        # of the simulation again and clear buffered out
        if self._buffer_manager is not None:
            self._buffer_manager.reset()

        # reset the current count of how many milliseconds the application
        # has ran for over multiple calls to run
        self._current_run_timesteps = 0

        # change number of resets as loading the binary again resets the sync\
        # to 0
        self._no_sync_changes = 0

        # sets the reset last flag to true, so that when run occurs, the tools
        # know to update the vertices which need to know a reset has occurred
        self._has_reset_last = True

    @staticmethod
    def _create_xml_paths():

        # add the extra xml files from the config file
        xml_paths = config.get("Mapping", "extra_xmls_paths")
        if xml_paths == "None":
            xml_paths = list()
        else:
            xml_paths = xml_paths.split(",")

        # add extra xml paths for pynn algorithms
        xml_paths.append(os.path.join(
            os.path.dirname(overridden_pacman_functions.__file__),
            "algorithms_metadata.xml"))
        xml_paths.extend(
            helpful_functions.get_front_end_common_pacman_xml_paths())
        return xml_paths

    def _calculate_number_of_machine_time_steps(self, next_run_timesteps):
        total_run_timesteps = next_run_timesteps
        if next_run_timesteps is not None:
            total_run_timesteps += self._current_run_timesteps
            machine_time_steps = (
                (total_run_timesteps * 1000.0) / self._machine_time_step)
            if machine_time_steps != int(machine_time_steps):
                logger.warn(
                    "The runtime and machine time step combination result in "
                    "a fractional number of machine time steps")
            self._no_machine_time_steps = int(math.ceil(machine_time_steps))
        else:
            self._no_machine_time_steps = None
            for vertex in self._partitionable_graph.vertices:
                if ((isinstance(vertex, AbstractSpikeRecordable) and
                        vertex.is_recording_spikes()) or
                        (isinstance(vertex, AbstractVRecordable) and
                            vertex.is_recording_v()) or
                        (isinstance(vertex, AbstractGSynRecordable) and
                            vertex.is_recording_gsyn)):
                    raise common_exceptions.ConfigurationException(
                        "recording a population when set to infinite runtime "
                        "is not currently supported")
        return total_run_timesteps

    def _detect_if_graph_has_changed(self, reset_flags=True):
        """ Iterates though the graph and looks changes
        """
        changed = False
        for population in self._populations:
            if population.requires_mapping:
                changed = True
            if reset_flags:
                population.mark_no_changes()

        for projection in self._projections:
            if projection.requires_mapping:
                changed = True
            if reset_flags:
                projection.mark_no_changes()

        return changed

    @property
    def has_ran(self):
        """

        :return:
        """
        return self._has_ran

    @property
    def machine_time_step(self):
        """

        :return:
        """
        return self._machine_time_step

    @property
    def no_machine_time_steps(self):
        """

        :return:
        """
        return self._no_machine_time_steps

    @property
    def timescale_factor(self):
        """

        :return:
        """
        return self._time_scale_factor

    @property
    def partitioned_graph(self):
        """

        :return:
        """
        return self._partitioned_graph

    @property
    def partitionable_graph(self):
        """

        :return:
        """
        return self._partitionable_graph

    @property
    def routing_infos(self):
        """

        :return:
        """
        return self._routing_infos

    @property
    def placements(self):
        """

        :return:
        """
        return self._placements

    @property
    def transceiver(self):
        """

        :return:
        """
        return self._txrx

    @property
    def graph_mapper(self):
        """

        :return:
        """
        return self._graph_mapper

    @property
    def min_supported_delay(self):
        """
        the min supported delay based in milliseconds
        :return:
        """
        return self._min_supported_delay

    @property
    def max_supported_delay(self):
        """
        the max supported delay based in milliseconds
        :return:
        """
        return self._max_supported_delay

    @property
    def buffer_manager(self):
        return self._buffer_manager

    def get_current_time(self):
        """

        :return:
        """
        if self._has_ran:
            return (
                float(self._current_run_timesteps) *
                (float(self._machine_time_step) / 1000.0))
        return 0.0

    def __repr__(self):
        return "Spinnaker object for machine {}".format(self._hostname)

    def add_vertex(self, vertex_to_add):
        """

        :param vertex_to_add:
        :return:
        """
        if isinstance(vertex_to_add, CommandSender):
            self._multi_cast_vertex = vertex_to_add

        self._partitionable_graph.add_vertex(vertex_to_add)

        if isinstance(vertex_to_add, AbstractSendMeMulticastCommandsVertex):
            if self._multi_cast_vertex is None:
                self._multi_cast_vertex = CommandSender(
                    self._machine_time_step, self._time_scale_factor)
                self.add_vertex(self._multi_cast_vertex)
            edge = MultiCastPartitionableEdge(
                self._multi_cast_vertex, vertex_to_add)
            self._multi_cast_vertex.add_commands(vertex_to_add.commands, edge)
            self.add_edge(edge)

        # add any dependent edges and vertices if needed
        if isinstance(vertex_to_add,
                      AbstractVertexWithEdgeToDependentVertices):
            for dependant_vertex in vertex_to_add.dependent_vertices:
                self.add_vertex(dependant_vertex)
                dependant_edge = MultiCastPartitionableEdge(
                    pre_vertex=vertex_to_add, post_vertex=dependant_vertex)
                self.add_edge(
                    dependant_edge,
                    vertex_to_add.edge_partition_identifier_for_dependent_edge)

    def add_edge(self, edge_to_add, partition_identifier=None,
                 partition_constraints=None):
        """

        :param edge_to_add:
        :param partition_identifier: the partition identifier for the outgoing
                    edge partition
        :param partition_constraints: the constraints of a partition
        associated with this edge
        :return:
        """
        self._partitionable_graph.add_edge(edge_to_add, partition_identifier,
                                           partition_constraints)

    def create_population(self, size, cellclass, cellparams, structure, label):
        """

        :param size:
        :param cellclass:
        :param cellparams:
        :param structure:
        :param label:
        :return:
        """
        return Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, spinnaker=self)

    def _add_population(self, population):
        """ Called by each population to add itself to the list
        """
        self._populations.append(population)

    def _add_projection(self, projection):
        """ called by each projection to add itself to the list
        :param projection:
        :return:
        """
        self._projections.append(projection)

    def create_projection(
            self, presynaptic_population, postsynaptic_population, connector,
            source, target, synapse_dynamics, label, rng):
        """

        :param presynaptic_population:
        :param postsynaptic_population:
        :param connector:
        :param source:
        :param target:
        :param synapse_dynamics:
        :param label:
        :param rng:
        :return:
        """
        if label is None:
            label = "Projection {}".format(self._edge_count)
            self._edge_count += 1
        return Projection(
            presynaptic_population=presynaptic_population, label=label,
            postsynaptic_population=postsynaptic_population, rng=rng,
            connector=connector, source=source, target=target,
            synapse_dynamics=synapse_dynamics, spinnaker_control=self,
            machine_time_step=self._machine_time_step,
            timescale_factor=self._time_scale_factor,
            user_max_delay=self.max_supported_delay)

    def stop(self, turn_off_machine=None, clear_routing_tables=None,
             clear_tags=None):
        """
        :param turn_off_machine: decides if the machine should be powered down\
            after running the execution. Note that this powers down all boards\
            connected to the BMP connections given to the transceiver
        :type turn_off_machine: bool
        :param clear_routing_tables: informs the tool chain if it\
            should turn off the clearing of the routing tables
        :type clear_routing_tables: bool
        :param clear_tags: informs the tool chain if it should clear the tags\
            off the machine at stop
        :type clear_tags: boolean
        :return: None
        """
        for population in self._populations:
            population._end()

        # if not a virtual machine, then shut down stuff on the board
        if not config.getboolean("Machine", "virtual_board"):

            if turn_off_machine is None:
                turn_off_machine = \
                    config.getboolean("Machine", "turn_off_machine")

            if clear_routing_tables is None:
                clear_routing_tables = config.getboolean(
                    "Machine", "clear_routing_tables")

            if clear_tags is None:
                clear_tags = config.getboolean("Machine", "clear_tags")

            # if stopping on machine, clear iptags and
            if clear_tags:
                for ip_tag in self._tags.ip_tags:
                    self._txrx.clear_ip_tag(
                        ip_tag.tag, board_address=ip_tag.board_address)
                for reverse_ip_tag in self._tags.reverse_ip_tags:
                    self._txrx.clear_ip_tag(
                        reverse_ip_tag.tag,
                        board_address=reverse_ip_tag.board_address)

            # if clearing routing table entries, clear
            if clear_routing_tables:
                for router_table in self._router_tables.routing_tables:
                    if not self._machine.get_chip_at(router_table.x,
                                                     router_table.y).virtual:
                        self._txrx.clear_multicast_routes(router_table.x,
                                                          router_table.y)

            # clear values
            self._no_sync_changes = 0

            # app stop command
            self._txrx.stop_application(self._app_id)

            if self._buffer_manager is not None:
                self._buffer_manager.stop()

            # stop the transceiver
            if turn_off_machine:
                logger.info("Turning off machine")
            self._txrx.close(power_off_machine=turn_off_machine)

    def _add_socket_address(self, socket_address):
        """

        :param socket_address:
        :return:
        """
        self._database_socket_addresses.add(socket_address)


# pacman imports
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.operations import algorithm_reports as pacman_algorithm_reports

# common front end imports
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utilities.report_states import ReportState
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.interface.executable_finder import ExecutableFinder

# local front end imports
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

# general imports
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
        self._partitioned_graph = None
        self._graph_mapper = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._tags = None
        self._machine = None
        self._txrx = None
        self._reports_states = None
        self._app_id = None
        self._buffer_manager = None

        # database objects
        self._database_socket_addresses = set()
        if database_socket_addresses is not None:
            self._database_socket_addresses.union(database_socket_addresses)
        self._database_interface = None
        self._create_database = None
        self._database_file_path = None

        # Determine default executable folder location
        # and add this default to end of list of search paths
        executable_finder.add_path(os.path.dirname(model_binaries.__file__))

        # population holders
        self._populations = list()
        self._projections = list()
        self._multi_cast_vertex = None
        self._edge_count = 0
        self._live_spike_recorder = dict()

        # holder for the executable targets (which we will need for reset and
        # pause and resume functionality
        self._executable_targets = None

        # holders for data needed for reset when nothing changes in the
        # application graph
        self._processor_to_app_data_base_address_mapper = None
        self._placement_to_app_data_file_paths = None
        self._dsg_targets = None

        # holder for timing related values
        self._has_ran = False
        self._has_reset_last = False
        self._current_run_ms = 0
        self._no_machine_time_steps = None
        self._machine_time_step = None
        self._no_sync_changes = 0
        self._steps = None
        self._original_first_run = None

        # state thats needed the first time around
        if self._app_id is None:
            self._app_id = config.getint("Machine", "appID")

            if config.getboolean("Reports", "reportsEnabled"):
                self._reports_states = ReportState(
                    config.getboolean("Reports", "writePartitionerReports"),
                    config.getboolean("Reports",
                                      "writePlacerReportWithPartitionable"),
                    config.getboolean("Reports",
                                      "writePlacerReportWithoutPartitionable"),
                    config.getboolean("Reports", "writeRouterReports"),
                    config.getboolean("Reports", "writeRouterInfoReport"),
                    config.getboolean("Reports", "writeTextSpecs"),
                    config.getboolean("Reports", "writeReloadSteps"),
                    config.getboolean("Reports", "writeTransceiverReport"),
                    config.getboolean("Reports", "outputTimesForSections"),
                    config.getboolean("Reports", "writeTagAllocationReports"))

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

        self._spikes_per_second = float(config.getfloat(
            "Simulation", "spikes_per_second"))
        self._ring_buffer_sigma = float(config.getfloat(
            "Simulation", "ring_buffer_sigma"))

        # set up machine targeted data
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)

        # if your using the auto pause and resume, then add the inputs needed
        # for this functionality.
        self._using_auto_pause_and_resume = \
            config.getboolean("Mode", "use_auto_pause_and_resume")

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

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
        """

        :param run_time:
        :return:
        """
        logger.info("Starting execution process")

        if self._original_first_run is None:
            self._original_first_run = run_time
        if self._has_reset_last and self._original_first_run != run_time:
            raise common_exceptions.ConfigurationException(
                "Currently spynnaker cannot reset and immediately handle a "
                "runtime that was not the same as the original run. Please "
                "run for {} ms and then change the runtime."
                .format(self._original_first_run))

        # get inputs
        inputs, application_graph_changed, uses_auto_pause_and_resume = \
            self._create_pacman_executor_inputs(run_time)

        if (self._original_first_run < run_time and
                not uses_auto_pause_and_resume):
            raise common_exceptions.ConfigurationException(
                "Currently spynnaker cannot handle a runtime greater than what"
                " was used during the initial run, unless you use the "
                "\" auto_pause_and_resume\" functionality. To turn this on, "
                " please go to your .spynnaker.cfg file and add "
                "[Mode] and use_auto_pause_and_resume = False")

        if application_graph_changed and self._has_ran:
            raise common_exceptions.ConfigurationException(
                "Changes to the application graph are not currently supported;"
                " please instead call p.reset(), p.end(), add changes and then"
                " call p.setup()")

        # if the application graph has changed and you've already ran, kill old
        # stuff running on machine
        if application_graph_changed and self._has_ran:
            self._txrx.stop_application(self._app_id)

        # get outputs
        required_outputs = self._create_pacman_executor_outputs(
            requires_reset=False,
            application_graph_changed=application_graph_changed)

        # algorithms listing
        algorithms, optional_algorithms = self._create_algorithm_list(
            config.get("Mode", "mode") == "Debug", application_graph_changed,
            executing_reset=False,
            using_auto_pause_and_resume=uses_auto_pause_and_resume)

        # xml paths to the algorithms metadata
        xml_paths = self._create_xml_paths()

        # run pacman executor
        pacman_exeuctor = helpful_functions.do_mapping(
            inputs, algorithms, optional_algorithms, required_outputs,
            xml_paths, config.getboolean("Reports", "outputTimesForSections"))

        # gather provenance data from the executor itself if needed
        if (config.getboolean("Reports", "writeProvenanceData") and
                not config.getboolean("Machine", "virtual_board")):
            pacman_executor_file_path = os.path.join(
                pacman_exeuctor.get_item("ProvenanceFilePath"),
                "PACMAN_provancence_data.xml")
            pacman_exeuctor.write_provenance_data_in_xml(
                pacman_executor_file_path,
                pacman_exeuctor.get_item("MemoryTransciever"))

        # sort out outputs data
        self._update_data_structures_from_pacman_exeuctor(
            pacman_exeuctor, application_graph_changed,
            uses_auto_pause_and_resume)

        # switch the reset last flag, as now the last thing to run is a run
        self._has_reset_last = False

    def reset(self):
        """ Code that puts the simulation back at time zero
        :return:
        """

        logger.info("Starting reset progress")

        inputs, application_graph_changed, using_auto_pause_and_resume = \
            self._create_pacman_executor_inputs(
                this_run_time=0, is_resetting=True)

        if self._has_ran and application_graph_changed:
            raise common_exceptions.ConfigurationException(
                "Resetting the simulation after changing the model"
                " is not supported")

        algorithms, optional_algorithms = self._create_algorithm_list(
            config.get("Mode", "mode") == "Debug", application_graph_changed,
            executing_reset=True,
            using_auto_pause_and_resume=using_auto_pause_and_resume)

        xml_paths = self._create_xml_paths()
        required_outputs = self._create_pacman_executor_outputs(
            requires_reset=True,
            application_graph_changed=application_graph_changed)

        # rewind the buffers from the buffer manager, to start at the beginning
        # of the simulation again and clear buffered out
        self._buffer_manager.reset()

        # reset the current count of how many milliseconds the application
        # has ran for over multiple calls to run
        self._current_run_ms = 0

        # change number of resets as loading the binary again resets the sync\
        # to 0
        self._no_sync_changes = 0

        # sets the has ran into false state, to pretend that its like it has
        # not ran
        self._has_ran = False

        # sets the reset last flag to true, so that when run occurs, the tools
        # know to update the vertices which need to know a reset has occurred
        self._has_reset_last = True

        # reset the n_machine_time_steps from each vertex
        for vertex in self.partitionable_graph.vertices:
            vertex.set_no_machine_time_steps(0)

        # execute reset functionality
        helpful_functions.do_mapping(
            inputs, algorithms, optional_algorithms, required_outputs,
            xml_paths, config.getboolean("Reports", "outputTimesForSections"))

        # if graph has changed kill all old objects as they will need to be
        # rebuilt at next run
        if application_graph_changed:
            self._placements = self._router_tables = self._routing_infos = \
                self._tags = self._graph_mapper = self._partitioned_graph = \
                self._database_interface = self._executable_targets = \
                self._placement_to_app_data_file_paths = \
                self._processor_to_app_data_base_address_mapper = None

    def _update_data_structures_from_pacman_exeuctor(
            self, pacman_exeuctor, application_graph_changed,
            uses_auto_pause_and_resume):
        """ Updates all the spinnaker local data structures that it needs from\
            the pacman executor
        :param pacman_exeuctor: the pacman executor required to extract data\
                structures from.
        :return:
        """
        if application_graph_changed:
            if not config.getboolean("Machine", "virtual_board"):
                self._txrx = pacman_exeuctor.get_item("MemoryTransciever")
                self._executable_targets = \
                    pacman_exeuctor.get_item("ExecutableTargets")
                self._buffer_manager = pacman_exeuctor.get_item("BufferManager")
                self._processor_to_app_data_base_address_mapper = \
                    pacman_exeuctor.get_item("ProcessorToAppDataBaseAddress")
                self._placement_to_app_data_file_paths = \
                    pacman_exeuctor.get_item("PlacementToAppDataFilePaths")

            self._placements = pacman_exeuctor.get_item("MemoryPlacements")
            self._router_tables = \
                pacman_exeuctor.get_item("MemoryRoutingTables")
            self._routing_infos = \
                pacman_exeuctor.get_item("MemoryRoutingInfos")
            self._tags = pacman_exeuctor.get_item("MemoryTags")
            self._graph_mapper = pacman_exeuctor.get_item("MemoryGraphMapper")
            self._partitioned_graph = \
                pacman_exeuctor.get_item("MemoryPartitionedGraph")
            self._machine = pacman_exeuctor.get_item("MemoryMachine")
            self._database_interface = \
                pacman_exeuctor.get_item("DatabaseInterface")
            self._database_file_path = \
                pacman_exeuctor.get_item("DatabaseFilePath")
            self._dsg_targets = \
                pacman_exeuctor.get_item("DataSpecificationTargets")

        if uses_auto_pause_and_resume:
            self._steps = pacman_exeuctor.get_item("Steps")

        # update stuff that alkways needed updating
        self._no_sync_changes = pacman_exeuctor.get_item("NoSyncChanges")
        self._has_ran = pacman_exeuctor.get_item("RanToken")
        if uses_auto_pause_and_resume:
            self._current_run_ms = \
                pacman_exeuctor.get_item("TotalCommunitiveRunTime")
        else:
            self._current_run_ms += pacman_exeuctor.get_item("RunTime")

    @staticmethod
    def _create_xml_paths():

        # add the extra xml files from the config file
        xml_paths = config.get("Mapping", "extra_xmls_paths")
        if xml_paths == "None":
            xml_paths = list()
        else:
            xml_paths = xml_paths.split(",")

        # add extra xml paths for pynn algorithms
        xml_paths.append(
            os.path.join(os.path.dirname(overridden_pacman_functions.__file__),
                         "algorithms_metadata.xml"))
        xml_paths.append(os.path.join(os.path.dirname(
            pacman_algorithm_reports.__file__), "reports_metadata.xml"))
        return xml_paths

    def _create_algorithm_list(
            self, in_debug_mode, application_graph_changed, executing_reset,
            using_auto_pause_and_resume):
        """
        creates the list of algorithms to use within the system
        :param in_debug_mode: if the tools should be operating in debug mode
        :param application_graph_changed: has the graph changed since last run
        :param executing_reset: are we executing a reset function
        :param using_auto_pause_and_resume: check if the system is to use
        auto pasue and resume functionality
        :return: list of algorithums to use and a list of optional
        algotihms to use
        """
        algorithms = list()
        optional_algorithms = list()

        # needed for multi-run/SSA's to work correctly.
        algorithms.append("SpyNNakerRuntimeUpdator")

        # add functions for updating the models
        algorithms.append("FrontEndCommonRuntimeUpdater")

        # if youve not ran before, add the buffer manager
        using_virtual_board = config.getboolean("Machine", "virtual_board")
        if application_graph_changed and not using_virtual_board:
            if not using_auto_pause_and_resume:
                optional_algorithms.append("FrontEndCommonBufferManagerCreater")

        # if you're needing a reset, you need to clean the binaries
        # (unless you've not ran yet)
        if executing_reset and self._has_ran:

            # kill binaries
            # TODO: when SARK 1.34 appears, this only needs to send a signal
            algorithms.append("FrontEndCommonApplicationExiter")

        # if the allocation graph has changed, need to go through mapping
        if application_graph_changed and not executing_reset:

            # if the system has ran before, kill the apps and run mapping
            # add debug algorithms if needed
            if in_debug_mode:
                algorithms.append("ValidRoutesChecker")

            algorithm_names = \
                config.get("Mapping", "algorithms")

            algorithm_strings = algorithm_names.split(",")
            for algorithm_string in algorithm_strings:
                split_string = algorithm_string.split(":")
                if len(split_string) == 1:
                    algorithms.append(split_string[0])
                else:
                    raise common_exceptions.ConfigurationException(
                        "The tool chain expects config params of list of 1 "
                        "element with ,. Where the elements are either: the "
                        "algorithm_name:algorithm_config_file_path, or "
                        "algorithm_name if its a internal to pacman algorithm."
                        " Please rectify this and try again")

            # if using virtual machine, add to list of algorithms the virtual
            # machine generator, otherwise add the standard machine generator
            if using_virtual_board:
                algorithms.append("FrontEndCommonVirtualMachineInterfacer")
            else:
                # protect against the situation where the system has already
                # got a transceiver (overriding does not lose sockets)
                if self._txrx is not None:
                    self._txrx.close()
                    self._txrx = None

                algorithms.append("FrontEndCommonMachineInterfacer")
                algorithms.append("FrontEndCommonNotificationProtocol")
                optional_algorithms.append("FrontEndCommonRoutingTableLoader")
                optional_algorithms.append("FrontEndCommonTagsLoader")

                # add algorithms that the auto supplies if not using it
                if not using_auto_pause_and_resume:
                    optional_algorithms.append(
                        "FrontEndCommonLoadExecutableImages")
                    algorithms.append("FrontEndCommonApplicationRunner")
                    optional_algorithms.append(
                        "FrontEndCommonApplicationDataLoader")
                    algorithms.append("FrontEndCommonPartitionableGraphHost"
                                      "ExecuteDataSpecification")
                    algorithms.append("FrontEndCommonLoadExecutableImages")
                    algorithms.append("FrontEndCommomPartitionableGraphData"
                                      "SpecificationWriter")
                else:
                    algorithms.append("FrontEndCommonAutoPauseAndResumer")

                # if the end user wants reload script, add the reload script
                # creator to the list (reload script currently only supported
                # for the original run)
                write_reload = config.getboolean("Reports", "writeReloadSteps")

                # if reload and auto pause and resume are on, raise exception
                if write_reload and using_auto_pause_and_resume:
                    raise common_exceptions.ConfigurationException(
                        "You cannot use auto pause and resume with a "
                        "reload script. This is due to reload not being able to"
                        "extract data from the machine. Please fix"
                        " and try again")

                # if first run, create reload
                if not self._has_ran and write_reload:
                    algorithms.append("FrontEndCommonReloadScriptCreator")

                # if ran before, warn that reload is only available for
                # first run
                elif self.has_ran and write_reload:
                    logger.warn(
                        "The reload script cannot handle multi-runs, nor can"
                        "it handle resets, therefore it will only contain the "
                        "initial run")

            if (config.getboolean("Reports", "writeMemoryMapReport")
                    and not using_virtual_board):
                algorithms.append("FrontEndCommonMemoryMapReport")

            if config.getboolean("Reports", "writeNetworkSpecificationReport"):
                algorithms.append(
                    "FrontEndCommonNetworkSpecificationPartitionableReport")

            # if going to write provenance data after the run add the two
            # provenance gatherers
            if (config.getboolean("Reports", "writeProvenanceData")
                    and not using_virtual_board):
                algorithms.append("FrontEndCommonProvenanceGatherer")

            # define mapping between output types and reports
            if self._reports_states is not None \
                    and self._reports_states.tag_allocation_report:
                algorithms.append("TagReport")
            if self._reports_states is not None \
                    and self._reports_states.routing_info_report:
                algorithms.append("routingInfoReports")
            if self._reports_states is not None \
                    and self._reports_states.router_report:
                algorithms.append("RouterReports")
            if self._reports_states is not None \
                    and self._reports_states.partitioner_report:
                algorithms.append("PartitionerReport")
            if (self._reports_states is not None and
                    self._reports_states.
                    placer_report_with_partitionable_graph):
                algorithms.append("PlacerReportWithPartitionableGraph")
            if (self._reports_states is not None and
                    self._reports_states.
                    placer_report_without_partitionable_graph):
                algorithms.append("PlacerReportWithoutPartitionableGraph")

        elif not executing_reset:
            # add function for extracting all the recorded data from
            # recorded populations
            if self._has_ran:
                algorithms.append("SpyNNakerRecordingExtractor")
            if not self._has_ran:
                optional_algorithms.append(
                    "FrontEndCommonApplicationDataLoader")
                algorithms.append("FrontEndCommonLoadExecutableImages")

            # add default algorithms
            algorithms.append("FrontEndCommonNotificationProtocol")

            # add functions for setting off the models again
            if using_auto_pause_and_resume:
                algorithms.append("FrontEndCommonAutoPauseAndResumer")
            else:
                algorithms.append("FrontEndCommonApplicationRunner")

            # if going to write provanence data after the run add the two
            # provenance gatherers
            if config.getboolean("Reports", "writeProvenanceData"):
                algorithms.append("FrontEndCommonProvenanceGatherer")

        return algorithms, optional_algorithms

    def _create_pacman_executor_outputs(
            self, requires_reset, application_graph_changed):

        # explicitly define what outputs spynnaker expects
        required_outputs = list()
        if config.getboolean("Machine", "virtual_board"):
            if application_graph_changed:
                required_outputs.extend([
                    "MemoryPlacements", "MemoryRoutingTables",
                    "MemoryRoutingInfos", "MemoryTags",
                    "MemoryPartitionedGraph", "MemoryGraphMapper"])
        else:
            if not requires_reset:
                required_outputs.append("RanToken")

        # if front end wants reload script, add requires reload token
        if (config.getboolean("Reports", "writeReloadSteps") and
                not self._has_ran and application_graph_changed and
                not config.getboolean("Machine", "virtual_board")):
            required_outputs.append("ReloadToken")
        return required_outputs

    def _create_pacman_executor_inputs(
            self, this_run_time, is_resetting=False):

        inputs = list()

        application_graph_changed, provenance_file_path, \
            self._no_sync_changes, no_machine_time_steps, json_folder, width, \
            height, number_of_boards, scamp_socket_addresses, boot_port_num, \
            using_auto_pause_and_resume, max_sdram_size = \
                self._deduce_standard_input_params(is_resetting, this_run_time)

        inputs = self._add_standard_basic_inputs(
            inputs, no_machine_time_steps, is_resetting, max_sdram_size,
            this_run_time)

        # if using auto_pause and resume, add basic pause and resume inputs
        if using_auto_pause_and_resume:
            inputs = self._add_auto_pause_and_resume_inputs(
                inputs, application_graph_changed, is_resetting)

        # FrontEndCommonApplicationDataLoader after a reset and no changes
        if not self._has_ran and not application_graph_changed:
            inputs = self._add_resetted_last_and_no_change_inputs(inputs)

        # support resetting when there's changes in the application graph
        # (only need to exit)
        if application_graph_changed and is_resetting:
            inputs = self._add_inputs_for_reset_with_changes(inputs)

        # mapping required
        elif application_graph_changed and not is_resetting:
            inputs = self._add_mapping_inputs(
                inputs, width, height, scamp_socket_addresses, boot_port_num,
                provenance_file_path, json_folder, number_of_boards)

            # if already ran, this is a remapping, thus needs to warn end user
            if self._has_ran:
                logger.warn(
                    "The network has changed, and therefore mapping will be"
                    " done again.  Any recorded data will be erased.")
        #
        else:
            inputs = self._add_extra_run_inputs(inputs, provenance_file_path)

        return inputs, application_graph_changed, using_auto_pause_and_resume

    def _deduce_standard_input_params(self, is_resetting, this_run_time):
        application_graph_changed = \
            self._detect_if_graph_has_changed(not is_resetting)

        # file path to store any provenance data to
        provenance_file_path = \
            os.path.join(self._report_default_directory, "provance_data")
        if not os.path.exists(provenance_file_path):
                os.mkdir(provenance_file_path)

        # all modes need the NoSyncChanges
        if application_graph_changed:
            self._no_sync_changes = 0

        # all modes need the runtime in machine time steps
        # (partitioner and rerun)
        no_machine_time_steps = \
            int(((this_run_time - self._current_run_ms) * 1000.0)
                / self._machine_time_step)

        # make a folder for the json files to be stored in
        json_folder = os.path.join(
            self._report_default_directory, "json_files")
        if not os.path.exists(json_folder):
            os.mkdir(json_folder)

        # translate config "None" to None
        width = config.get("Machine", "width")
        height = config.get("Machine", "height")
        if width == "None":
            width = None
        else:
            width = int(width)
        if height == "None":
            height = None
        else:
            height = int(height)

        number_of_boards = config.get("Machine", "number_of_boards")
        if number_of_boards == "None":
            number_of_boards = None

        scamp_socket_addresses = config.get("Machine",
                                            "scamp_connections_data")
        if scamp_socket_addresses == "None":
            scamp_socket_addresses = None

        boot_port_num = config.get("Machine", "boot_connection_port_num")
        if boot_port_num == "None":
            boot_port_num = None
        else:
            boot_port_num = int(boot_port_num)

        # if your using the auto pause and resume, then add the inputs needed
        # for this functionality.
        using_auto_pause_and_resume = \
            config.getboolean("Mode", "use_auto_pause_and_resume")

        # used for debug purposes to fix max size of sdram each chip has
        max_sdram_size = config.get("Machine", "max_sdram_allowed_per_chip")
        if max_sdram_size == "None":
            max_sdram_size = None
        else:
            max_sdram_size = int(max_sdram_size)

        return \
            application_graph_changed, provenance_file_path, \
            self._no_sync_changes, no_machine_time_steps, json_folder, width,\
            height, number_of_boards, scamp_socket_addresses, boot_port_num, \
            using_auto_pause_and_resume, max_sdram_size

    def _add_extra_run_inputs(self, inputs, provenance_file_path):
        # mapping does not need to be executed, therefore add
        # the data elements needed for the application runner and
        # runtime re-setter
        inputs.append({
            "type": "BufferManager",
            "value": self._buffer_manager})
        inputs.append({
            'type': "DatabaseWaitOnConfirmationFlag",
            'value': config.getboolean("Database", "wait_on_confirmation")})
        inputs.append({
            'type': "SendStartNotifications",
            'value': config.getboolean("Database", "send_start_notification")})
        inputs.append({
            'type': "DatabaseInterface",
            'value': self._database_interface})
        inputs.append({
            "type": "DatabaseSocketAddresses",
            'value': self._database_socket_addresses})
        inputs.append({
            'type': "DatabaseFilePath",
            'value': self._database_file_path})
        inputs.append({
            'type': "ExecutableTargets",
            'value': self._executable_targets})
        inputs.append({
            'type': "APPID",
            'value': self._app_id})
        inputs.append({
            "type": "MemoryTransciever",
            'value': self._txrx})
        inputs.append({
            'type': "TimeScaleFactor",
            'value': self._time_scale_factor})
        inputs.append({
            'type': "LoadedReverseIPTagsToken",
            'value': True})
        inputs.append({
            'type': "LoadedIPTagsToken",
            'value': True})
        inputs.append({
            'type': "LoadedRoutingTablesToken",
            'value': True})
        inputs.append({
            'type': "LoadBinariesToken",
            'value': True})
        inputs.append({
            'type': "LoadedApplicationDataToken",
            'value': True})
        inputs.append({
            'type': "MemoryPlacements",
            'value': self._placements})
        inputs.append({
            'type': "MemoryGraphMapper",
            'value': self._graph_mapper})
        inputs.append({
            'type': "MemoryPartitionableGraph",
            'value': self._partitionable_graph})
        inputs.append({
            'type': "MemoryExtendedMachine",
            'value': self._machine})
        inputs.append({
            'type': "MemoryRoutingTables",
            'value': self._router_tables})
        inputs.append({
            'type': "ProvenanceFilePath",
            'value': provenance_file_path})
        inputs.append({
            'type': "RanToken",
            'value': self._has_ran})
        return inputs

    def _add_mapping_inputs(
            self, inputs, width, height, scamp_socket_addresses, boot_port_num,
            provenance_file_path, json_folder, number_of_boards):

        # basic input stuff
        inputs.append({
            'type': "MemoryPartitionableGraph",
            'value': self._partitionable_graph})
        inputs.append({
            'type': 'ReportFolder',
            'value': self._report_default_directory})
        inputs.append({
            'type': 'IPAddress',
            'value': self._hostname})
        inputs.append({
            'type': "BMPDetails",
            'value': config.get("Machine", "bmp_names")})
        inputs.append({
            'type': "DownedChipsDetails",
            'value': config.get("Machine", "down_chips")})
        inputs.append({
            'type': "DownedCoresDetails",
            'value': config.get("Machine", "down_cores")})
        inputs.append({
            'type': "BoardVersion",
            'value': config.getint("Machine", "version")})
        inputs.append({
            'type': "NumberOfBoards",
            'value': number_of_boards})
        inputs.append({
            'type': "MachineWidth",
            'value': width})
        inputs.append({
            'type': "MachineHeight",
            'value': height})
        inputs.append({
            'type': "AutoDetectBMPFlag",
            'value': config.getboolean("Machine", "auto_detect_bmp")})
        inputs.append({
            'type': "EnableReinjectionFlag",
            'value': config.getboolean("Machine", "enable_reinjection")})
        inputs.append({
            'type': "ScampConnectionData",
            'value': scamp_socket_addresses})
        inputs.append({
            'type': "BootPortNum",
            'value': boot_port_num})
        inputs.append({
            'type': "APPID",
            'value': self._app_id})
        inputs.append({
            'type': "TimeScaleFactor",
            'value': self._time_scale_factor})
        inputs.append({
            'type': "DatabaseSocketAddresses",
            'value': self._database_socket_addresses})
        inputs.append({
            'type': "DatabaseWaitOnConfirmationFlag",
            'value': config.getboolean("Database", "wait_on_confirmation")})
        inputs.append({
            'type': "WriteTextSpecsFlag",
            'value': config.getboolean("Reports", "writeTextSpecs")})
        inputs.append({
            'type': "ExecutableFinder",
            'value': executable_finder})
        inputs.append({
            'type': "MachineHasWrapAroundsFlag",
            'value': config.getboolean("Machine", "requires_wrap_arounds")})
        inputs.append({
            'type': "ReportStates",
            'value': self._reports_states})
        inputs.append({
            'type': "UserCreateDatabaseFlag",
            'value': config.get("Database", "create_database")})
        inputs.append({
            'type': "ExecuteMapping",
            'value': config.getboolean(
                "Database", "create_routing_info_to_neuron_id_mapping")})
        inputs.append({
            'type': "SendStartNotifications",
            'value': config.getboolean("Database", "send_start_notification")})
        inputs.append({
            'type': "ProvenanceFilePath",
            'value': provenance_file_path})

        # add paths for each file based version
        inputs.append({
            'type': "FileCoreAllocationsFilePath",
            'value': os.path.join(json_folder, "core_allocations.json")})
        inputs.append({
            'type': "FileSDRAMAllocationsFilePath",
            'value': os.path.join(json_folder, "sdram_allocations.json")})
        inputs.append({
            'type': "FileMachineFilePath",
            'value': os.path.join(json_folder, "machine.json")})
        inputs.append({
            'type': "FilePartitionedGraphFilePath",
            'value': os.path.join(json_folder, "partitioned_graph.json")})
        inputs.append({
            'type': "FilePlacementFilePath",
            'value': os.path.join(json_folder, "placements.json")})
        inputs.append({
            'type': "FileRouingPathsFilePath",
            'value': os.path.join(json_folder, "routing_paths.json")})
        inputs.append({'type': "FileConstraintsFilePath",
                       'value': os.path.join(json_folder, "constraints.json")})
        return inputs

    def _add_inputs_for_reset_with_changes(self, inputs):
        inputs.append({
            "type": "MemoryTransciever",
            'value': self._txrx})
        inputs.append({
            'type': "ExecutableTargets",
            'value': self._executable_targets})
        inputs.append({
            'type': "MemoryPlacements",
            'value': self._placements})
        inputs.append({
            'type': "MemoryGraphMapper",
            'value': self._graph_mapper})
        inputs.append({
            'type': "APPID",
            'value': self._app_id})
        inputs.append({
            'type': "RanToken",
            'value': self._has_ran})
        return inputs

    def _add_standard_basic_inputs(
            self, inputs, no_machine_time_steps, is_resetting, max_sdram_size,
            this_run_time):

        # support resetting the machine during start up
        reset_machine_on_startup = \
            config.getboolean("Machine", "reset_machine_on_startup")
        needs_to_reset_machine = \
            (reset_machine_on_startup and not self._has_ran
             and not is_resetting)

        inputs.append({
            'type': "RunTime",
            'value': this_run_time})
        inputs.append({
            'type': "TotalCommunitiveRunTime",
            'value': self._current_run_ms})
        inputs.append({
            'type': "UseAutoPauseAndResume",
            'value': True})
        inputs.append({
            'type': "MaxSDRAMSize",
            'value': max_sdram_size})
        inputs.append({
            'type': "NoSyncChanges",
            'value': self._no_sync_changes})
        inputs.append({
            'type': "RunTimeMachineTimeSteps",
            'value': no_machine_time_steps})
        inputs.append({
            'type': "MachineTimeStep",
            'value': self._machine_time_step})
        inputs.append({
            "type": "ResetMachineOnStartupFlag",
            'value': needs_to_reset_machine})
        # stuff most versions need
        inputs.append({
            'type': "WriteCheckerFlag",
            'value': config.getboolean("Mode", "verify_writes")})
        inputs.append({
            'type': "ReportStates",
            'value': self._reports_states})
        inputs.append({
            'type': "ApplicationDataFolder",
            'value': self._app_data_runtime_folder})

        return inputs

    def _add_resetted_last_and_no_change_inputs(self, inputs):
        inputs.append(({
            'type': "ProcessorToAppDataBaseAddress",
            "value": self._processor_to_app_data_base_address_mapper}))
        inputs.append({
            "type": "PlacementToAppDataFilePaths",
            'value': self._placement_to_app_data_file_paths})
        inputs.append({
            'type': "WriteCheckerFlag",
            'value': config.getboolean("Mode", "verify_writes")})
        return inputs

    def _add_auto_pause_and_resume_inputs(
            self, inputs, application_graph_changed, is_resetting):
        # due to the mismatch between dsg's and dse's in different front
        # end, the inputs not given to the multile pause and resume but
        # which are needed for dsg/dse need to be put in the extra inputs

        spynnaker_xml_file = os.path.join(
            os.path.dirname(overridden_pacman_functions.__file__),
            "algorithms_metadata.xml")
        extra_xmls = list()
        extra_xmls.append(spynnaker_xml_file)

        extra_inputs = list()
        extra_inputs.append({
            'type': 'ExecutableFinder',
            'value': executable_finder})
        extra_inputs.append({
            'type': 'IPAddress',
            'value': self._hostname})
        extra_inputs.append({
            'type': 'ReportFolder',
            'value': self._report_default_directory})
        extra_inputs.append({
            'type': 'WriteTextSpecsFlag',
            'value': config.getboolean("Reports", "writeTextSpecs")})
        extra_inputs.append({
            'type': 'ApplicationDataFolder',
            'value': self._app_data_runtime_folder})
        extra_inputs.append({
            'type': "TotalCommunitiveRunTime",
            'value': self._current_run_ms})
        extra_inputs.append({
            'type': "MachineTimeStep",
            'value': self._machine_time_step})

        # standard inputs
        inputs.append({
            'type': "ExtraAlgorithms",
            'value': ["SpyNNakerRecordingExtractor",
                      "SpyNNakerRuntimeUpdatorAfterRun"]})
        inputs.append({
            'type': "ExtraInputs",
            'value': extra_inputs})
        inputs.append({
            'type': "ExtraXMLS",
            'value': extra_xmls})
        inputs.append({
            'type': "DSGeneratorAlgorithm",
            'value': "FrontEndCommomPartitionableGraphDataSpecificationWriter"})
        inputs.append({
            'type': "DSExecutorAlgorithm",
            'value':
                "FrontEndCommonPartitionableGraphHostExecuteDataSpecification"})
        inputs.append({
            'type': "HasRanBefore",
            'value': self._has_ran})
        inputs.append({
            'type': "ApplicationGraphChanged",
            'value': application_graph_changed})
        inputs.append({
            'type': "HasResetBefore",
            'value': self._has_reset_last})
        inputs.append({
            'type': "Steps",
            'value': self._steps})

        # add extra needed by auto_pause and resume if reset has occurred
        if not application_graph_changed and not is_resetting:
            inputs.append({
                'type': "MemoryRoutingInfos",
                'value': self._routing_infos})
            inputs.append({
                'type': "MemoryPartitionedGraph",
                'value': self._partitioned_graph})
            inputs.append({
                'type': "MemoryTags",
                'value': self._tags})
            extra_inputs.append({
                'type': "LoadedApplicationDataToken",
                'value': True})
            extra_inputs.append({
                'type': "ExecutableTargets",
                'value': self._executable_targets})
            extra_inputs.append({
                'type': "DataSpecificationTargets",
                'value': self._dsg_targets})
            extra_inputs.append({
                'type': "ProcessorToAppDataBaseAddress",
                'value':self._processor_to_app_data_base_address_mapper})
            extra_inputs.append({
                'type': "PlacementToAppDataFilePaths",
                'value':self._placement_to_app_data_file_paths})
            extra_inputs.append({
                'type': "LoadBinariesToken",
                'value': True})

        # multi run mode
        if not application_graph_changed and self._has_ran:
            extra_inputs.append({
                'type': "LoadBinariesToken",
                'value': True})
            extra_inputs.append({
                'type': "RanToken",
                'value': True})
        if self._buffer_manager is not None:
            extra_inputs.append({
                'type': "BufferManager",
                'value': self._buffer_manager})

        return inputs

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
    def app_id(self):
        """

        :return:
        """
        return self._app_id

    @property
    def using_auto_pause_and_resume(self):
        """

        :return:
        """
        return self._using_auto_pause_and_resume

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
    def writing_reload_script(self):
        """
        returns if the system is to use auto_pause and resume
        :return:
        """
        return config.getboolean("Reports", "writeReloadSteps")

    @property
    def timescale_factor(self):
        """

        :return:
        """
        return self._time_scale_factor

    @property
    def spikes_per_second(self):
        """

        :return:
        """
        return self._spikes_per_second

    @property
    def ring_buffer_sigma(self):
        """

        :return:
        """
        return self._ring_buffer_sigma

    @property
    def get_multi_cast_source(self):
        """

        :return:
        """
        return self._multi_cast_vertex

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
    def routing_infos(self):
        """

        :return:
        """
        return self._routing_infos

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

    def set_app_id(self, value):
        """

        :param value:
        :return:
        """
        self._app_id = value

    def get_current_time(self):
        """

        :return:
        """
        if self._has_ran:
            return float(self._current_run_ms)
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

    def add_edge(self, edge_to_add, partition_identifier=None):
        """

        :param edge_to_add:
        :param partition_identifier: the partition identifier for the outgoing\
                    edge partition
        :return:
        """
        self._partitionable_graph.add_edge(edge_to_add, partition_identifier)

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

            if self._create_database:
                self._database_interface.stop()

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

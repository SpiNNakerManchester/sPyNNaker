"""
Spinnaker
"""

# pacman imports
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.operations import algorithm_reports as pacman_algorithm_reports

# common front end imports
from spinn_front_end_common.interface.interface_functions.\
    front_end_common_application_exiter import \
    FrontEndCommonApplicationExiter
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utilities.report_states import ReportState
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.interface.executable_finder import ExecutableFinder

# local front end imports
from spynnaker.pyNN.models.common.abstract_gsyn_recordable import \
    AbstractGSynRecordable
from spynnaker.pyNN.models.common.abstract_v_recordable import \
    AbstractVRecordable
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

# general imports
import logging
import math
import os

logger = logging.getLogger(__name__)

executable_finder = ExecutableFinder()


class Spinnaker(object):
    """
    Spinnaker
    """

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
        self._has_ran = False
        self._has_resetted_last = False
        self._reports_states = None
        self._app_id = None
        self._current_run_ms = None
        self._buffer_manager = None
        
        # database objects
        self._database_socket_addresses = set()
        if database_socket_addresses is not None:
            self._database_socket_addresses.union(database_socket_addresses)
        self._database_interface = None
        self._create_database = None

        # Determine default executable folder location
        # and add this default to end of list of search paths
        executable_finder.add_path(os.path.dirname(model_binaries.__file__))

        # population holders
        self._populations = list()
        self._projections = list()
        self._multi_cast_vertex = None
        self._edge_count = 0
        self._live_spike_recorder = dict()

        # holder for the exeuctable targets (which we will need for reset and
        # pause and resume functionality
        self._executable_targets = None

        # holders for data needed for reset when nothing changes in the
        # application graph
        self._processor_to_app_data_base_address_mapper = None
        self._vertex_to_app_data_file_paths = None

        # holder for timing related values
        self._no_machine_time_steps = None
        self._machine_time_step = None
        self._no_sync_changes = 0

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

        # set up machine targetted data
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

    def _set_up_machine_specifics(self, timestep, min_delay, max_delay,
                                  hostname):
        self._machine_time_step = config.getint("Machine", "machineTimeStep")

        # deal with params allowed via the setup optimals
        if timestep is not None:
            timestep *= 1000  # convert into ms from microseconds
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
        logger.info("Starting exeuction process")

        # calculate number of machine time steps
        total_run_time = self._calculate_number_of_machine_time_steps(run_time)

        self._current_run_ms = run_time

        # get inputs
        inputs, application_graph_changed = \
            self._create_pacman_executor_inputs(total_run_time)

        # if the application graph has changed and youve already ran, kill old
        # stuff running on machine
        if application_graph_changed and self._has_ran:
            exiter = FrontEndCommonApplicationExiter()
            exiter(self._app_id, self._txrx, self._executable_targets,
                   self._no_sync_changes)

        # get outputs
        required_outputs = \
            self._create_pacman_executor_outputs(
                requires_reset=self._has_resetted_last,
                application_graph_changed=application_graph_changed)
        # algorithms listing
        algorithms = self._create_algorithm_list(
            config.get("Mode", "mode") == "Debug", application_graph_changed,
            requires_reset=False)
        # xml paths to the algorthims metadata
        xml_paths = self._create_xml_paths()
        # run pacman exeuctor
        pacman_exeuctor = helpful_functions.do_mapping(
            inputs, algorithms, required_outputs, xml_paths,
            config.getboolean("Reports", "outputTimesForSections"))

        # gather provenance data from the executor itself if needed
        if config.get("Reports", "writeProvanceData"):
            pacman_executor_file_path = os.path.join(
                pacman_exeuctor.get_item("ProvenanceFilePath"),
                "PACMAN_provancence_data.xml")
            pacman_exeuctor.write_provenance_data_in_xml(
                pacman_executor_file_path,
                pacman_exeuctor.get_item("MemoryTransciever"))

        # sort out outputs datas
        if application_graph_changed:
            self._update_data_structures_from_pacman_exeuctor(pacman_exeuctor)
        else:
            self._no_sync_changes = pacman_exeuctor.get_item("NoSyncChanges")

        # reset the reset flag to say the last thing was not a reset call
        self._has_resetted_last = False
        self._current_run_ms = total_run_time

    def _update_data_structures_from_pacman_exeuctor(self, pacman_exeuctor):
        """
        updates all the spinnaker local data structs that it needs from the
        pacman exeuctor
        :param pacman_exeuctor: the pacman exectuor required to extract data
            structs from.
        :return:
        """
        self._txrx = pacman_exeuctor.get_item("MemoryTransciever")
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
        self._has_ran = pacman_exeuctor.get_item("RanToken")
        self._executable_targets = \
            pacman_exeuctor.get_item("ExecutableTargets")
        self._buffer_manager = pacman_exeuctor.get_item("BufferManager")
        self._processor_to_app_data_base_address_mapper = \
            pacman_exeuctor.get_item("ProcessorToAppDataBaseAddress")
        self._vertex_to_app_data_file_paths = \
            pacman_exeuctor.get_item("VertexToAppDataFilePaths")
        self._no_sync_changes = pacman_exeuctor.get_item("NoSyncChanges")

    def reset(self):
        """
        code that puts the simulation back at time zero
        :return:
        """

        logger.info("Starting reset progress")

        self._has_resetted_last = True
        inputs, application_graph_changed = self._create_pacman_executor_inputs(
                reset=self._has_resetted_last, total_runtime=0)
        algorithms = self._create_algorithm_list(
            config.get("Mode", "mode") == "Debug", application_graph_changed,
            requires_reset=self._has_resetted_last)
        xml_paths = self._create_xml_paths()
        required_outputs = self._create_pacman_executor_outputs(
            requires_reset=self._has_resetted_last,
            application_graph_changed=application_graph_changed)

        # rewind the buffers from the buffer manager, to start at the beginning
        # of the simulation again
        self._buffer_manager.rewind()

        # reset the current count of how many milliseconds the application
        # has ran for over multiple calls to run
        self._current_run_ms = 0

        # change num of resets as loading the binary again resets the sync to 0
        self._no_sync_changes = 0

        # reset the n_machien time steps from each vertex
        for vertex in self.partitionable_graph.vertices:
            vertex.set_no_machine_time_steps(0)
            if (isinstance(vertex, AbstractSpikeRecordable)
                    or isinstance(vertex, AbstractVRecordable)
                    or isinstance(vertex, AbstractGSynRecordable)):
                vertex.reset()

        # TODO there needs to be some decision on reload here.

        # execute reset functionality
        pacman_exeuctor = helpful_functions.do_mapping(
            inputs, algorithms, required_outputs, xml_paths,
            config.getboolean("Reports", "outputTimesForSections"))

        # if the application graph changed reset the data structures
        if application_graph_changed:
            self._update_data_structures_from_pacman_exeuctor(pacman_exeuctor)

    @staticmethod
    def _create_xml_paths():
        # add the extra xml files from the cfg file
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

    def _create_algorithm_list(self, in_debug_mode, application_graph_changed,
                               requires_reset):
        algorithms = list()

        # if youve not ran before, add the buffer manager
        if not self._has_ran:
                algorithms.append("FrontEndCommonBufferManagerCreater")

        # if your needing qa reset, you need to clean the binairies
        # (unless youve not ran yet)
        if requires_reset and not self._has_ran:
                # kill binaries
                algorithms.append("FrontEndCommonApplicationExiter")

        # if needs a reset but no applciation graph has changed, then you
        # need to reload the app data and executable images
        if requires_reset and not application_graph_changed:
            algorithms.append(
                "FrontEndCommonPartitionableGraphApplicationDataLoader")
            # load binairies back on
            algorithms.append("FrontEndCommomLoadExecutableImages")

        # if the allication graph has changed, need to go through mapping
        if application_graph_changed:

            # if the system has ran before, kill the apps and run mapping
            # add debug algorithms if needed
            if in_debug_mode:
                algorithms.append("ValidRoutesChecker")
                
            algorithm_names = \
                config.get("Mapping", "algorithms") + "," + \
                config.get("Mapping", "interface_algorithms")

            algorithm_strings = algorithm_names.split(",")
            for algorithm_string in algorithm_strings:
                split_string = algorithm_string.split(":")
                if len(split_string) == 1:
                    algorithms.append(split_string[0])
                else:
                    raise common_exceptions.ConfigurationException(
                        "The tool chain expects config params of list of 1 "
                        "element with ,. Where the elements are either: the "
                        "algorithum_name:algorithm_config_file_path, or "
                        "algorithum_name if its a interal to pacman algorithm."
                        " Please rectify this and try again")

            # if using virutal machine, add to list of algorithms the virtual
            # machine generator, otherwise add the standard machine generator
            if config.getboolean("Machine", "virtual_board"):
                algorithms.append("FrontEndCommonVirtualMachineInterfacer")
            else:
                algorithms.append("FrontEndCommonMachineInterfacer")
                algorithms.append("FrontEndCommonApplicationRunner")
    
                # if the end user wants reload script, add the reload script
                # creator to the list (reload script currently only supported 
                # for the original run)
                # TODO look at this for multiple runs
                if (not self._has_ran 
                        and config.getboolean("Reports", "writeReloadSteps")):
                    algorithms.append("FrontEndCommonReloadScriptCreator")
    
            if config.getboolean("Reports", "writeMemoryMapReport"):
                algorithms.append("FrontEndCommonMemoryMapReport")
    
            if config.getboolean("Reports", "writeNetworkSpecificationReport"):
                algorithms.append(
                    "FrontEndCommonNetworkSpecificationPartitionableReport")

            # if going to write provanence data after the run add the two
            # provenance gatherers
            if config.get("Reports", "writeProvanceData"):
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
        else:
            # add function for extracting all the recorded data from
            # recorded populations
            if not self._has_resetted_last:
                algorithms.append("SpyNNakerRecordingExtracter")
                # add functions for updating the models
            algorithms.append("FrontEndCommonRuntimeUpdater")
            # add functions for setting off the models again
            algorithms.append("FrontEndCommonApplicationRunner")
            # if going to write provanence data after the run add the two
            # provenance gatherers
            if config.get("Reports", "writeProvanceData"):
                algorithms.append("FrontEndCommonProvenanceGatherer")
        return algorithms

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
        if (config.getboolean("Reports", "writeReloadSteps")
                and not self._has_ran):
            required_outputs.append("ReloadToken")
        return required_outputs

    def _create_pacman_executor_inputs(self, total_runtime, reset=False):

        application_graph_changed = self._detect_if_graph_has_changed()
        inputs = list()

        # file path to store any provenance data to
        provenance_file_path = os.path.join(self._report_default_directory,
                                            "provance_data")
        if not os.path.exists(provenance_file_path):
                os.mkdir(provenance_file_path)

        if application_graph_changed:

            # the application graph has changed, so new binaries are being
            # loaded and therefore sync mode starts at zero again.
            self._no_sync_changes = 0

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

            inputs.append({'type': "MemoryPartitionableGraph",
                           'value': self._partitionable_graph})
            inputs.append({'type': 'ReportFolder',
                           'value': self._report_default_directory})
            inputs.append({'type': "ApplicationDataFolder",
                           'value': self._app_data_runtime_folder})
            inputs.append({'type': 'IPAddress', 'value': self._hostname})

            # basic input stuff
            inputs.append({'type': "BMPDetails",
                           'value': config.get("Machine", "bmp_names")})
            inputs.append({'type': "DownedChipsDetails",
                           'value': config.get("Machine", "down_chips")})
            inputs.append({'type': "DownedCoresDetails",
                           'value': config.get("Machine", "down_cores")})
            inputs.append({'type': "BoardVersion",
                           'value': config.getint("Machine", "version")})
            inputs.append({'type': "NumberOfBoards",
                           'value': number_of_boards})
            inputs.append({'type': "MachineWidth", 'value': width})
            inputs.append({'type': "MachineHeight", 'value': height})
            inputs.append({'type': "AutoDetectBMPFlag",
                           'value': config.getboolean("Machine",
                                                      "auto_detect_bmp")})
            inputs.append({'type': "EnableReinjectionFlag",
                           'value': config.getboolean("Machine",
                                                      "enable_reinjection")})
            inputs.append({'type': "ScampConnectionData",
                           'value': scamp_socket_addresses})
            inputs.append({'type': "BootPortNum", 'value': boot_port_num})
            inputs.append({'type': "APPID", 'value': self._app_id})
            inputs.append({'type': "RunTime", 'value': self._current_run_ms})
            inputs.append({'type': "TimeScaleFactor",
                           'value': self._time_scale_factor})
            inputs.append({'type': "MachineTimeStep",
                           'value': self._machine_time_step})
            inputs.append({'type': "DatabaseSocketAddresses",
                           'value': self._database_socket_addresses})
            inputs.append({'type': "DatabaseWaitOnConfirmationFlag",
                           'value': config.getboolean(
                               "Database", "wait_on_confirmation")})
            inputs.append({'type': "WriteCheckerFlag",
                           'value': config.getboolean(
                               "Mode", "verify_writes")})
            inputs.append({'type': "WriteTextSpecsFlag",
                           'value': config.getboolean(
                               "Reports", "writeTextSpecs")})
            inputs.append({'type': "ExecutableFinder",
                           'value': executable_finder})
            inputs.append({'type': "MachineHasWrapAroundsFlag",
                           'value': config.getboolean(
                               "Machine", "requires_wrap_arounds")})
            inputs.append({'type': "ReportStates",
                           'value': self._reports_states})
            inputs.append({'type': "UserCreateDatabaseFlag",
                           'value': config.get("Database", "create_database")})
            inputs.append({'type': "ExecuteMapping",
                           'value':  config.getboolean(
                               "Database",
                               "create_routing_info_to_neuron_id_mapping")})
            inputs.append({'type': "DatabaseSocketAddresses",
                           'value': self._database_socket_addresses})
            inputs.append({'type': "SendStartNotifications",
                           'value': config.getboolean(
                               "Database", "send_start_notification")})
            inputs.append({'type': "ProvenanceFilePath",
                           'value': provenance_file_path})

            # add paths for each file based version
            inputs.append({'type': "FileCoreAllocationsFilePath",
                           'value': os.path.join(
                               json_folder, "core_allocations.json")})
            inputs.append({'type': "FileSDRAMAllocationsFilePath",
                           'value': os.path.join(
                               json_folder, "sdram_allocations.json")})
            inputs.append({'type': "FileMachineFilePath",
                           'value': os.path.join(
                               json_folder, "machine.json")})
            inputs.append({'type': "FilePartitionedGraphFilePath",
                           'value':os.path.join(
                               json_folder, "partitioned_graph.json")})
            inputs.append({'type': "FilePlacementFilePath",
                           'value': os.path.join(
                               json_folder, "placements.json")})
            inputs.append({'type': "FileRouingPathsFilePath",
                           'value': os.path.join(
                               json_folder, "routing_paths.json")})
            inputs.append({'type': "FileConstraintsFilePath",
                           'value': os.path.join(
                               json_folder, "constraints.json")})
            inputs.append({"type": "LoadInitialBuffersFlag",
                           "value": True})
            inputs.append({'type': "NoSyncChanges",
                           'value': self._no_sync_changes})
            if self._has_ran:
                logger.warn(
                    "The graph has changed since the original graph was loaded "
                    "and ran. Therefore decisions made during the mapping "
                    "process will be incorrect now, and therefore mapping "
                    "needs to be redone. Sorry. Please note that any "
                    "recorded data will also have been lost. If you were "
                    "wanting this daya, please rerun your script and extract"
                    "the data before recalling run. Thank you")
                inputs.append({'type': "BufferManager",
                               'value': self._buffer_manager})
        else:
            # mapping does not need to be executed, therefore add
            # the data elements needed for the application runner and
            # runtime resetter
            inputs.append({"type": "BufferManager",
                           "value": self._buffer_manager})
            inputs.append({'type': "DatabaseWaitOnConfirmationFlag",
                           'value': config.getboolean(
                               "Database", "wait_on_confirmation")})
            inputs.append({'type': "SendStartNotifications",
                           'value': config.getboolean(
                               "Database", "send_start_notification")})
            inputs.append({'type': "DatabaseInterface",
                           'value': self._database_interface})
            inputs.append({'type': "ExecutableTargets",
                           'value': self._executable_targets})
            inputs.append({'type': "APPID", 'value': self._app_id})
            inputs.append({"type": "MemoryTransciever",
                           'value': self._txrx})
            inputs.append({"type": "RunTime",
                           'value': self._current_run_ms})
            inputs.append({'type': "TimeScaleFactor",
                           'value': self._time_scale_factor})
            inputs.append({'type': "LoadedReverseIPTagsToken",
                           'value': True})
            inputs.append({'type': "LoadedIPTagsToken", 'value': True})
            inputs.append({'type': "LoadedRoutingTablesToken",
                           'value': True})
            inputs.append({'type': "LoadBinariesToken", 'value': True})
            inputs.append({'type': "LoadedApplicationDataToken",
                           'value': True})
            inputs.append({'type': "MemoryPlacements",
                           'value': self._placements})
            inputs.append({'type': "MemoryGraphMapper",
                           'value': self._graph_mapper})
            inputs.append({'type': "NoSyncChanges",
                           'value': self._no_sync_changes})
            inputs.append({'type': "MemoryPartitionableGraph",
                           'value': self._partitionable_graph})
            inputs.append({'type': "MemoryExtendedMachine",
                           'value': self._machine})
            inputs.append({'type': "MemoryRoutingTables",
                           'value': self._router_tables})
            inputs.append({'type': "ProvenanceFilePath",
                           'value': provenance_file_path})
            inputs.append({'type': "BufferManager",
                           'value': self._buffer_manager})

        if self._has_ran and not reset:
            no_machine_time_steps =\
                int(((total_runtime - self._current_run_ms) * 1000.0)
                    / self._machine_time_step)
            inputs.append({'type': "RunTimeMachineTimeSteps",
                           'value': no_machine_time_steps})
            inputs.append({"type": "LoadInitialBuffersFlag", "value": False})
        if self._has_ran and reset:
            inputs.append(({
                'type': "ProcessorToAppDataBaseAddress",
                "value": self._processor_to_app_data_base_address_mapper}))
            inputs.append({"type": "VertexToAppDataFilePaths",
                           'value': self._vertex_to_app_data_file_paths})
            inputs.append({'type': "WriteCheckerFlag",
                           'value': config.getboolean(
                               "Mode", "verify_writes")})

        return inputs, application_graph_changed

    def _calculate_number_of_machine_time_steps(self, next_run_time):
        if next_run_time is not None:
            if self._current_run_ms is not None:
                next_run_time += self._current_run_ms
            self._no_machine_time_steps =\
                int((next_run_time * 1000.0) / self._machine_time_step)
            ceiled_machine_time_steps = \
                math.ceil((next_run_time * 1000.0) / self._machine_time_step)
            if self._no_machine_time_steps != ceiled_machine_time_steps:
                raise common_exceptions.ConfigurationException(
                    "The runtime and machine time step combination result in "
                    "a factional number of machine runable time steps and "
                    "therefore spinnaker cannot determine how many to run for")
            for vertex in self._partitionable_graph.vertices:
                if isinstance(vertex, AbstractDataSpecableVertex):
                    vertex.set_no_machine_time_steps(
                        self._no_machine_time_steps)
        else:
            self._no_machine_time_steps = None
            logger.warn("You have set a runtime that will never end, this may "
                        "cause the neural models to fail to partition "
                        "correctly")
            for vertex in self._partitionable_graph.vertices:
                if ((isinstance(vertex, AbstractSpikeRecordable) and
                        vertex.is_recording_spikes())
                        or (isinstance(vertex, AbstractVRecordable) and
                            vertex.is_recording_v())
                        or (isinstance(vertex, AbstractGSynRecordable) and
                            vertex.is_recording_gsyn)):
                    raise common_exceptions.ConfigurationException(
                        "recording a population when set to infinite runtime "
                        "is not currently supportable in this tool chain. "
                        "watch this space")
        return next_run_time
                
    def _detect_if_graph_has_changed(self):
        """
        iterates though the graph and looks for asks if they have changed
        :return:
        """
        changed = False
        for population in self._populations:
            if population.change_requires_mapping:
                # ask the vertex if this change requires mapping to be redone
                if population._vertex.change_requires_mapping:
                    changed = True
                    population._vertex.change_requires_mapping = False
                population.change_requires_mapping = False
        for projection in self._projections:
            if projection.change_requires_mapping:
                if (projection._delay_edge is not None
                        and projection._delay_edge.change_requires_mapping):
                    changed = True
                    projection._delay_edge.change_requires_mapping = False
                if (projection._projection_edge is not None
                        and projection._projection_edge.
                            change_requires_mapping):
                    changed = True
                    projection._projection_edge.change_requires_mapping = False
                projection.change_requires_mapping = False
        return changed   

    @property
    def app_id(self):
        """

        :return:
        """
        return self._app_id

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

        # add any dependent edges and verts if needed
        if isinstance(vertex_to_add,
                      AbstractVertexWithEdgeToDependentVertices):
            for dependant_vertex in vertex_to_add.dependent_vertices:
                self.add_vertex(dependant_vertex)
                dependant_edge = MultiCastPartitionableEdge(
                    pre_vertex=vertex_to_add, post_vertex=dependant_vertex)
                self.add_edge(dependant_edge)

    def add_edge(self, edge_to_add, partition_identifier=None):
        """

        :param edge_to_add:
        :param partition_identifier: the partition identfer for the outgoing
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
            after running the exeuction. Note that this powers down all boards\
            connected to the BMP connections given to the transciever
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
            # stop the binaries that are in some state
            exiter = FrontEndCommonApplicationExiter()
            exiter(self._app_id, self._txrx, self._executable_targets,
                   self._no_sync_changes)

            # clear values
            self._no_sync_changes = 0

            # app stop command (currently fucked)
            #self._txrx.stop_application(self._app_id)
            if self._create_database:
                self._database_interface.stop()

            self._buffer_manager.stop()

            # stop the transciever
            if turn_off_machine:
                logger.info("Turning off machine")
            self._txrx.close(power_off_machine=turn_off_machine)

    def _add_socket_address(self, socket_address):
        """

        :param socket_address:
        :return:
        """
        self._database_socket_addresses.add(socket_address)

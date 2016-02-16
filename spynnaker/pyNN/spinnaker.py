
# pacman imports
from pacman.interfaces.abstract_provides_provenance_data import \
    AbstractProvidesProvenanceData
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.operations import algorithm_reports as pacman_algorithm_reports
from pacman.operations.pacman_algorithm_executor import PACMANAlgorithmExecutor
from pacman.utilities.utility_objs.provenance_data_item import \
    ProvenanceDataItem

# common front end imports
from spinn_front_end_common.interface.interface_functions.\
    front_end_common_execute_mapper import \
    FrontEndCommonExecuteMapper
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utilities.utility_objs.\
    provenance_data_items import ProvenanceDataItems
from spinn_front_end_common.utilities.utility_objs.report_states \
    import ReportState
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.interface.executable_finder import ExecutableFinder
from spinn_front_end_common.interface import interface_functions

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
from spynnaker.pyNN import _version


# general imports
import logging
import math
import os

logger = logging.getLogger(__name__)

executable_finder = ExecutableFinder()


class Spinnaker(AbstractProvidesProvenanceData):

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
        self._provenance_data_items = ProvenanceDataItems()
        self._provenance_file_path = None

        # holders for data needed for reset when nothing changes in the
        # application graph
        self._processor_to_app_data_base_address_mapper = None
        self._placement_to_app_data_file_paths = None

        # holder for timing related values
        self._has_ran = False
        self._has_reset_last = False
        self._current_run_ms = 0
        self._no_machine_time_steps = None
        self._machine_time_step = None
        self._no_sync_changes = 0

        # holder for algorithms to check for prov if crashed
        algorithms_listing = \
            config.get("Reports", "algorithms_to_get_prov_after_crash")
        self._algorithms_to_catch_prov_on_crash = algorithms_listing.split(",")

        # state that's needed the first time around
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
                    config.getboolean("Reports", "writeTagAllocationReports"),
                    config.getboolean("Reports", "writeRouterTableReports"))

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

            # set up provenance data folder
            self._provenance_file_path = \
                os.path.join(self._report_default_directory, "provenance_data")
            if not os.path.exists(self._provenance_file_path):
                    os.mkdir(self._provenance_file_path)

        self._spikes_per_second = float(config.getfloat(
            "Simulation", "spikes_per_second"))
        self._ring_buffer_sigma = float(config.getfloat(
            "Simulation", "ring_buffer_sigma"))

        # set up machine targeted data
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
        delay_extension_max_supported_delay = \
            constants.MAX_DELAY_BLOCKS \
            * constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK

        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extension_max_supported_delay

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
            logger.warn("The machine name from PyNN setup is overriding the "
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

        # calculate number of machine time steps
        total_run_time = self._calculate_number_of_machine_time_steps(run_time)

        # Calculate the first machine time step to start from and set this
        # where necessary
        first_machine_time_step = int(math.ceil(
            (self._current_run_ms * 1000.0) / self._machine_time_step))
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractHasFirstMachineTimeStep):
                vertex.set_first_machine_time_step(first_machine_time_step)

        # get inputs
        inputs, application_graph_changed = \
            self._create_pacman_executor_inputs(run_time)

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
        algorithms = self._create_algorithm_list(
            config.get("Mode", "mode") == "Debug", application_graph_changed,
            executing_reset=False)

        # xml paths to the algorithms metadata
        xml_paths = self._create_xml_paths()

        # run pacman executor
        execute_mapper = FrontEndCommonExecuteMapper()
        pacman_executor = execute_mapper.do_mapping(
            inputs, algorithms, required_outputs, xml_paths,
            config.getboolean("Reports", "outputTimesForSections"),
            self._algorithms_to_catch_prov_on_crash,
            prov_path=self._provenance_file_path)

        # sort out outputs data
        if application_graph_changed:
            self._update_data_structures_from_pacman_executor(pacman_executor)
        else:
            self._no_sync_changes = pacman_executor.get_item("NoSyncChanges")
            self._has_ran = pacman_executor.get_item("RanToken")

        # reset the reset flag to say the last thing was not a reset call
        self._current_run_ms = total_run_time

        # switch the reset last flag, as now the last thing to run is a run
        self._has_reset_last = False

        # gather provenance data from the executor itself if needed
        if config.get("Reports", "writeProvenanceData"):

            # get pacman provenance items
            prov_items = pacman_executor.get_provenance_data_items(
                pacman_executor.get_item("MemoryTransciever"))
            self._provenance_data_items.add_provenance_item_by_operation(
                "PACMAN", prov_items)
            # get spynnaker provenance
            prov_items = self.get_provenance_data_items(
                pacman_executor.get_item("MemoryTransciever"))
            self._provenance_data_items.add_provenance_item_by_operation(
                "sPyNNaker", prov_items)

    def reset(self):
        """ Code that puts the simulation back at time zero
        :return:
        """

        logger.info("Starting reset progress")

        inputs, application_graph_changed = \
            self._create_pacman_executor_inputs(
                this_run_time=0, is_resetting=True)

        if self._has_ran and application_graph_changed:
            raise common_exceptions.ConfigurationException(
                "Resetting the simulation after changing the model"
                " is not supported")

        algorithms = self._create_algorithm_list(
            config.get("Mode", "mode") == "Debug", application_graph_changed,
            executing_reset=True)
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
        execute_mapper = FrontEndCommonExecuteMapper()
        execute_mapper.do_mapping(
            inputs, algorithms, required_outputs, xml_paths,
            config.getboolean("Reports", "outputTimesForSections"),
            self._algorithms_to_catch_prov_on_crash,
            prov_path=self._provenance_file_path)

        # if graph has changed kill all old objects as they will need to be
        # rebuilt at next run
        if application_graph_changed:
            self._placements = self._router_tables = self._routing_infos = \
                self._tags = self._graph_mapper = self._partitioned_graph = \
                self._database_interface = self._executable_targets = \
                self._placement_to_app_data_file_paths = \
                self._processor_to_app_data_base_address_mapper = None

    def _update_data_structures_from_pacman_executor(self, pacman_executor):
        """ Updates all the spinnaker local data structures that it needs from\
            the pacman executor
        :param pacman_executor: the pacman executor required to extract data\
                structures from.
        :return:
        """
        if not config.getboolean("Machine", "virtual_board"):
            self._txrx = pacman_executor.get_item("MemoryTransciever")
            self._has_ran = pacman_executor.get_item("RanToken")
            self._executable_targets = \
                pacman_executor.get_item("ExecutableTargets")
            self._buffer_manager = pacman_executor.get_item("BufferManager")
            self._processor_to_app_data_base_address_mapper = \
                pacman_executor.get_item("ProcessorToAppDataBaseAddress")
            self._placement_to_app_data_file_paths = \
                pacman_executor.get_item("PlacementToAppDataFilePaths")

        self._placements = pacman_executor.get_item("MemoryPlacements")
        self._router_tables = \
            pacman_executor.get_item("MemoryRoutingTables")
        self._routing_infos = \
            pacman_executor.get_item("MemoryRoutingInfos")
        self._tags = pacman_executor.get_item("MemoryTags")
        self._graph_mapper = pacman_executor.get_item("MemoryGraphMapper")
        self._partitioned_graph = \
            pacman_executor.get_item("MemoryPartitionedGraph")
        self._machine = pacman_executor.get_item("MemoryMachine")
        self._database_interface = \
            pacman_executor.get_item("DatabaseInterface")
        self._database_file_path = \
            pacman_executor.get_item("DatabaseFilePath")
        self._no_sync_changes = pacman_executor.get_item("NoSyncChanges")

    def get_provenance_data_items(self, transceiver, placement=None):
        """
        @implements pacman.interface.abstract_provides_provenance_data.AbstractProvidesProvenanceData.get_provenance_data_items
        :return:
        """
        prov_items = list()
        prov_items.append(ProvenanceDataItem(
            name="ip_address",
            item=str(self._hostname)))
        prov_items.append(ProvenanceDataItem(
            name="software_version",
            item="{}:{}:{}:{}".format(
                _version.__version__,  _version.__version_name__,
                _version.__version_year__, _version.__version_month__)))
        prov_items.append(ProvenanceDataItem(
            name="machine_time_step",
            item=str(self._machine_time_step)))
        prov_items.append(ProvenanceDataItem(
            name="time_scale_factor",
            item=str(self._time_scale_factor)))
        prov_items.append(ProvenanceDataItem(
            name="total_runtime",
            item=str(self._current_run_ms)))
        return prov_items

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
            self, in_debug_mode, application_graph_changed, executing_reset):
        algorithms = list()

        # if you've not ran before, add the buffer manager
        if (application_graph_changed and
                not config.getboolean("Machine", "virtual_board")):
            algorithms.append("FrontEndCommonBufferManagerCreater")

        # if you're needing a reset, you need to clean the binaries
        # (unless you've not ran yet)
        if executing_reset and self._has_ran:

            # kill binaries
            # TODO: when SARK 1.34 appears, this only needs to send a signal
            algorithms.append("FrontEndCommonApplicationExiter")

        # if the allocation graph has changed, need to go through mapping
        if application_graph_changed and not executing_reset:

            # define mapping between output types and reports
            if self._reports_states is not None \
                    and self._reports_states.tag_allocation_report:
                algorithms.append("TagReport")
            if self._reports_states is not None \
                    and self._reports_states.routing_info_report:
                algorithms.append("routingInfoReports")
                algorithms.append("unCompressedRoutingTableReports")
            if self._reports_states is not None \
                    and self._reports_states.generate_routing_table_report:
                algorithms.append("compressedRoutingTableReports")
                algorithms.append("comparisonOfRoutingTablesReport")
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
            if config.getboolean("Machine", "virtual_board"):
                algorithms.append("FrontEndCommonVirtualMachineGenerator")
            else:
                # protect against the situation where the system has already
                # got a transceiver (overriding does not lose sockets)
                if self._txrx is not None:
                    self._txrx.close()
                    self._txrx = None

                algorithms.append("FrontEndCommonMachineInterfacer")
                algorithms.append("FrontEndCommonApplicationRunner")
                algorithms.append("FrontEndCommonNotificationProtocol")
                algorithms.append(
                    "FrontEndCommonPartitionableGraphApplicationDataLoader")
                algorithms.append("FrontEndCommonPartitionableGraphHost"
                                  "ExecuteDataSpecification")
                algorithms.append("FrontEndCommomLoadExecutableImages")
                algorithms.append("FrontEndCommonRoutingTableLoader")
                algorithms.append("FrontEndCommonTagsLoader")
                algorithms.append("FrontEndCommomPartitionableGraphData"
                                  "SpecificationWriter")

                # if the end user wants reload script, add the reload script
                # creator to the list (reload script currently only supported
                # for the original run)
                if (not self._has_ran and
                        config.getboolean("Reports", "writeReloadSteps")):
                    algorithms.append("FrontEndCommonReloadScriptCreator")
                elif (self.has_ran and
                        config.getboolean("Reports", "writeReloadSteps")):
                    logger.warn(
                        "The reload script cannot handle multi-runs, nor can"
                        "it handle resets, therefore it will only contain the "
                        "initial run")

            if (config.getboolean("Reports", "writeMemoryMapReport") and
                    not config.getboolean("Machine", "virtual_board")):
                algorithms.append("FrontEndCommonMemoryMapReport")

            if config.getboolean("Reports", "writeNetworkSpecificationReport"):
                algorithms.append(
                    "FrontEndCommonNetworkSpecificationPartitionableReport")

            # define mapping between output types and reports
            if self._reports_states is not None \
                    and self._reports_states.tag_allocation_report:
                algorithms.append("TagReport")
            if self._reports_states is not None \
                    and self._reports_states.routing_info_report:
                algorithms.append("routingInfoReports")
                algorithms.append("unCompressedRoutingTableReports")
                algorithms.append("compressedRoutingTableReports")
                algorithms.append("comparisonOfRoutingTablesReport")
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
            if self._has_ran and not executing_reset:
                algorithms.append("SpyNNakerRecordingExtractor")

                # add functions for updating the models
                algorithms.append("FrontEndCommonRuntimeUpdater")
            if not self._has_ran and not executing_reset:
                algorithms.append(
                    "FrontEndCommonPartitionableGraphApplicationDataLoader")
                algorithms.append("FrontEndCommomLoadExecutableImages")
            if not executing_reset:
                algorithms.append("FrontEndCommonNotificationProtocol")

                # add functions for setting off the models again
                algorithms.append("FrontEndCommonApplicationRunner")

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
        if (config.getboolean("Reports", "writeReloadSteps") and
                not self._has_ran and application_graph_changed and
                not config.getboolean("Machine", "virtual_board")):
            required_outputs.append("ReloadToken")
        return required_outputs

    def _create_pacman_executor_inputs(
            self, this_run_time, is_resetting=False):

        application_graph_changed = \
            self._detect_if_graph_has_changed(not is_resetting)
        inputs = list()

        # all modes need the NoSyncChanges
        if application_graph_changed:
            self._no_sync_changes = 0
        inputs.append(
            {'type': "NoSyncChanges", 'value': self._no_sync_changes})

        inputs.append(
            {'type': 'TimeTheshold',
             'value': config.getint("Machine", "time_to_wait_till_error")})

        # support resetting the machine during start up
        if (config.getboolean("Machine", "reset_machine_on_startup") and
                not self._has_ran and not is_resetting):
            inputs.append(
                {"type": "ResetMachineOnStartupFlag", 'value': True})
        else:
            inputs.append(
                {"type": "ResetMachineOnStartupFlag", 'value': False})

        # support runtime updater
        if self._has_ran and not is_resetting:
            no_machine_time_steps =\
                int((this_run_time * 1000.0) /
                    self._machine_time_step)
            inputs.append({'type': "RunTimeMachineTimeSteps",
                           'value': no_machine_time_steps})

        # FrontEndCommonPartitionableGraphApplicationDataLoader after a
        # reset and no changes
        if not self._has_ran and not application_graph_changed:
            inputs.append(({
                'type': "ProcessorToAppDataBaseAddress",
                "value": self._processor_to_app_data_base_address_mapper}))
            inputs.append({"type": "PlacementToAppDataFilePaths",
                           'value': self._placement_to_app_data_file_paths})
            inputs.append({'type': "WriteCheckerFlag",
                           'value': config.getboolean(
                               "Mode", "verify_writes")})

        # support resetting when there's changes in the application graph
        # (only need to exit)
        if application_graph_changed and is_resetting:
            inputs.append({"type": "MemoryTransciever", 'value': self._txrx})
            inputs.append({'type': "ExecutableTargets",
                           'value': self._executable_targets})
            inputs.append({'type': "MemoryPlacements",
                           'value': self._placements})
            inputs.append({'type': "MemoryGraphMapper",
                           'value': self._graph_mapper})
            inputs.append({'type': "APPID", 'value': self._app_id})
            inputs.append({'type': "RanToken", 'value': self._has_ran})

        elif application_graph_changed and not is_resetting:

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

            version = config.get("Machine", "version")
            if version == "None":
                version = None
            else:
                version = int(version)

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
                           'value': version})
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
            inputs.append({'type': "RunTime", 'value': this_run_time})
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
                           'value': config.getboolean(
                               "Database",
                               "create_routing_info_to_neuron_id_mapping")})
            inputs.append({'type': "DatabaseSocketAddresses",
                           'value': self._database_socket_addresses})
            inputs.append({'type': "SendStartNotifications",
                           'value': config.getboolean(
                               "Database", "send_start_notification")})

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
                           'value': os.path.join(
                               json_folder, "partitioned_graph.json")})
            inputs.append({'type': "FilePlacementFilePath",
                           'value': os.path.join(
                               json_folder, "placements.json")})
            inputs.append({'type': "FileRoutingPathsFilePath",
                           'value': os.path.join(
                               json_folder, "routing_paths.json")})
            inputs.append({'type': "FileConstraintsFilePath",
                           'value': os.path.join(
                               json_folder, "constraints.json")})

            if self._has_ran:
                logger.warn(
                    "The network has changed, and therefore mapping will be"
                    " done again.  Any recorded data will be erased.")
        else:
            # mapping does not need to be executed, therefore add
            # the data elements needed for the application runner and
            # runtime re-setter
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
            inputs.append({"type": "DatabaseSocketAddresses",
                           'value': self._database_socket_addresses})
            inputs.append({'type': "DatabaseFilePath",
                           'value': self._database_file_path})
            inputs.append({'type': "ExecutableTargets",
                           'value': self._executable_targets})
            inputs.append({'type': "APPID", 'value': self._app_id})
            inputs.append({"type": "MemoryTransciever", 'value': self._txrx})
            inputs.append({"type": "RunTime",
                           'value': this_run_time})
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
            inputs.append({'type': "MemoryPartitionableGraph",
                           'value': self._partitionable_graph})
            inputs.append({'type': "MemoryExtendedMachine",
                           'value': self._machine})
            inputs.append({'type': "MemoryRoutingTables",
                           'value': self._router_tables})
            inputs.append({'type': "RanToken", 'value': self._has_ran})

        return inputs, application_graph_changed

    def _calculate_number_of_machine_time_steps(self, next_run_time):
        total_run_time = next_run_time
        if next_run_time is not None:
            total_run_time += self._current_run_ms
            machine_time_steps = (
                (total_run_time * 1000.0) / self._machine_time_step)
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
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractDataSpecableVertex):
                vertex.set_no_machine_time_steps(self._no_machine_time_steps)
        return total_run_time

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

        # if operating in debug mode, extract io buffers from all machine
        self._run_debug_iobuf_extraction_for_exit(
            config.get("Mode", "mode") == "Debug")

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
            if config.getboolean("Machine", "use_app_stop"):
                self._txrx.stop_application(self._app_id)

            if self._create_database:
                self._database_interface.stop()

            self._buffer_manager.stop()

            # stop the transceiver
            if turn_off_machine:
                logger.info("Turning off machine")
            self._txrx.close(power_off_machine=turn_off_machine)

    def _run_debug_iobuf_extraction_for_exit(self, in_debug_mode):

        pacman_inputs = list()
        pacman_inputs.append({
            'type': "MemoryTransciever",
            'value': self._txrx})
        pacman_inputs.append({
            'type': "RanToken",
            'value': True})
        pacman_inputs.append({
            'type': "MemoryPlacements",
            'value': self._placements})
        pacman_inputs.append({
            'type': "ProvenanceFilePath",
            'value': self._provenance_file_path})
        pacman_inputs.append({
            'type': "ProvenanceItems",
            'value': self._provenance_data_items})
        pacman_inputs.append({
            'type': "MemoryRoutingTables",
            'value': self._router_tables})
        pacman_inputs.append({
            'type': "MemoryExtendedMachine",
            'value': self._machine})
        pacman_inputs.append({
            'type': "MemoryMachine",
            'value': self._machine})
        pacman_inputs.append({
            'type': 'FileMachineFilePath',
            'value': os.path.join(self._provenance_file_path,
                                  "Machine.json")})


        pacman_outputs = list()
        if in_debug_mode:
            pacman_outputs.append("FileMachine")
            pacman_outputs.append("ErrorMessages")
            pacman_outputs.append("IOBuffers")
        pacman_outputs.append("ProvenanceItems")

        pacman_algorithms = list()
        pacman_algorithms.append("FrontEndCommonProvenanceGatherer")
        pacman_algorithms.append("FrontEndCommonProvenanceXMLWriter")
        if in_debug_mode:
            pacman_algorithms.append("FrontEndCommonIOBufExtractor")
            pacman_algorithms.append("FrontEndCommonWarningGenerator")
            pacman_algorithms.append("FrontEndCommonMessagePrinter")
        pacman_xmls = list()
        pacman_xmls.append(
            os.path.join(os.path.dirname(interface_functions.__file__),
                         "front_end_common_interface_functions.xml"))
        pacman_executor = PACMANAlgorithmExecutor(
            algorithms=pacman_algorithms, inputs=pacman_inputs,
            xml_paths=pacman_xmls, required_outputs=pacman_outputs)
        pacman_executor.execute_mapping()

    def _add_socket_address(self, socket_address):
        """

        :param socket_address:
        :return:
        """
        self._database_socket_addresses.add(socket_address)

"""
Spinnaker
"""

# pacman imports
from pacman.model.partitionable_graph.partitionable_graph import \
    PartitionableGraph
from pacman.operations.pacman_algorithm_executor import PACMANAlgorithmExecutor
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.utilities.utility_objs.progress_bar import ProgressBar

# spinnmachine imports
from spinn_front_end_common.utilities.executable_targets import \
    ExecutableTargets
from spinn_machine.virutal_machine import VirtualMachine

# common front end imports
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utilities import reports
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.interface.\
    front_end_common_spinnman_interface_functions \
    import FrontEndCommonSpinnmanInterfaceFunctions
from spinn_front_end_common.interface.front_end_common_configuration_functions\
    import FrontEndCommonConfigurationFunctions
from pacman.utilities.utility_objs.timer import Timer
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.interface.executable_finder import ExecutableFinder
from spinn_front_end_common.interface.\
    front_end_common_provenance_functions import \
    FrontEndCommonProvenanceFunctions
from pacman.interfaces.abstract_provides_provenance_data import \
    AbstractProvidesProvenanceData

# local front end imports
from spynnaker.pyNN.models\
    .abstract_models.abstract_population_recordable_vertex import \
    AbstractPopulationRecordableVertex
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN import overridden_pacman_functions
from spynnaker.pyNN.spynnaker_configurations import \
    SpynnakerConfigurationFunctions
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import exceptions
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.models.abstract_models\
    .abstract_send_me_multicast_commands_vertex \
    import AbstractSendMeMulticastCommandsVertex
from spynnaker.pyNN.models.abstract_models\
    .abstract_vertex_with_dependent_vertices \
    import AbstractVertexWithEdgeToDependentVertices
from spynnaker.pyNN.utilities.database.spynnaker_database_writer import \
    SpynnakerDataBaseWriter

# general imports
import logging
import math
import os


logger = logging.getLogger(__name__)

executable_finder = ExecutableFinder()


class Spinnaker(FrontEndCommonConfigurationFunctions,
                FrontEndCommonSpinnmanInterfaceFunctions,
                FrontEndCommonProvenanceFunctions,
                SpynnakerConfigurationFunctions):
    """
    Spinnaker
    """

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None,
                 database_socket_addresses=None):
        FrontEndCommonConfigurationFunctions.__init__(self, host_name,
                                                      graph_label)
        SpynnakerConfigurationFunctions.__init__(self)
        FrontEndCommonProvenanceFunctions.__init__(self)

        # pacman objects
        self._partitionable_graph = None
        self._partitioned_graph = None
        self._graph_mapper = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._tags = None
        # set up the pacman executor
        self._pacman_exeuctor = None
        
        # database objects
        self._database_socket_addresses = set()
        self._database_interface = None
        self._create_database = None
        self._populations = list()
        
        self._database_interface = None

        if self._app_id is None:
            self._set_up_main_objects(
                app_id=config.getint("Machine", "appID"),
                execute_data_spec_report=config.getboolean(
                    "Reports", "writeTextSpecs"),
                execute_partitioner_report=config.getboolean(
                    "Reports", "writePartitionerReports"),
                execute_placer_report_with_partitionable_graph=
                config.getboolean("Reports",
                                  "writePlacerReportWithPartitionable"),
                execute_placer_report_without_partitionable_graph=
                config.getboolean("Reports",
                                  "writePlacerReportWithoutPartitionable"),
                reports_are_enabled=config.getboolean(
                    "Reports", "reportsEnabled"),
                generate_performance_measurements=config.getboolean(
                    "Reports", "outputTimesForSections"),
                execute_router_report=config.getboolean(
                    "Reports", "writeRouterReports"),
                execute_write_reload_steps=config.getboolean(
                    "Reports", "writeReloadSteps"),
                generate_transciever_report=config.getboolean(
                    "Reports", "writeTransceiverReport"),
                execute_routing_info_report=config.getboolean(
                    "Reports", "writeRouterInfoReport"),
                generate_tag_report=config.getboolean(
                    "Reports", "writeTagAllocationReports"))

            # set up exeuctable specifics
            self._set_up_executable_specifics()
            self._set_up_report_specifics(
                default_report_file_path=config.get(
                    "Reports", "defaultReportFilePath"),
                max_reports_kept=config.getint("Reports", "max_reports_kept"),
                reports_are_enabled=config.getboolean(
                    "Reports", "reportsEnabled"),
                write_provance_data=config.getboolean(
                    "Reports", "writeProvanceData"),
                write_text_specs=config.getboolean(
                    "Reports", "writeTextSpecs"))
            self._set_up_output_application_data_specifics(
                max_application_binaries_kept=config.getint(
                    "Reports", "max_application_binaries_kept"),
                where_to_write_application_data_files=config.get(
                    "Reports", "defaultApplicationDataFilePath"))

        # initilise the partitionable graph
        self._partitionable_graph = PartitionableGraph(label=graph_label)

        # set up machine targetted data
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)
        self._spikes_per_second = float(config.getfloat(
            "Simulation", "spikes_per_second"))
        self._ring_buffer_sigma = float(config.getfloat(
            "Simulation", "ring_buffer_sigma"))

        FrontEndCommonSpinnmanInterfaceFunctions.__init__(
            self, self._reports_states, self._report_default_directory,
        self._app_data_runtime_folder)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

        # Determine default executable folder location
        # and add this default to end of list of search paths
        executable_finder.add_path(os.path.dirname(model_binaries.__file__))
        self._edge_count = 0

        # Manager of buffered sending
        self._send_buffer_manager = None

        # holder for number of times the timer event should exuecte for the sim
        self._no_machine_time_steps = None

    def do_mapping(self, do_timings):
        """
        sets up
        :param do_timings: bool which sattes if each algorithm should time itself
        :return:mapper executor for this front end
        """
        # set up the mapper executor side of the front end
        # set up the pacman algorithms
        inputs = set()
        inputs.add("MemoryPartitionableGraph")
        inputs.add('MemoryMachine')
        inputs.add('ReportFolder')
        inputs.add('IPAddress')
        inputs.add("Transciever")
        # add paths for each file based version
        inputs.add("FileCoreAllocationsFilePath")
        inputs.add("FileSDRAMAllocationsFilePath")
        inputs.add("FileMachineFilePath")
        inputs.add("FilePartitionedGraphFilePath")
        inputs.add("FilePlacementFilePath")
        inputs.add("FileRouingPathsFilePath")
        inputs.add("FileConstraintsFilePath")

        # explicitly define what outputs spynnaker expects
        required_outputs = (
            "MemoryPlacements", "MemoryRoutingTables", "MemoryRoutingInfos",
            "MemoryTags", "MemoryPartitionedGraph", "MemoryGraphMapper")

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

        # get report states
        pacman_report_state = \
            self._reports_states.generate_pacman_report_states()
        in_debug_mode = config.get("Mode", "mode") == "Debug"

        # create executor
        self._pacman_exeuctor = PACMANAlgorithmExecutor(
            reports_states=pacman_report_state, in_debug_mode=in_debug_mode,
            do_timings=do_timings, inputs=inputs, xml_paths=xml_paths,
            algorithms=config.get("Mapping", "algorithms"),
            required_outputs=required_outputs)

        # define inputs
        inputs = list()
        inputs.append({'type': "MemoryPartitionableGraph",
                       'value': self._partitionable_graph})
        inputs.append({'type': 'MemoryMachine',
                       'value': self._machine})
        inputs.append({'type': "ReportFolder",
                       'value': self._report_default_directory})
        inputs.append({'type': "ApplicationDataFolder",
                       'value': self._app_data_runtime_folder})
        inputs.append({'type': "IPAddress", 'value': self._hostname})
        inputs.append({'type': "MemoryTransciever", 'value': self._txrx})

        # make a folder for the json files to be stored in
        json_folder = os.path.join(self._report_default_directory, "json_files")
        if not os.path.isdir(json_folder):
            os.mkdir(json_folder)

        # file paths for each json file
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
        inputs.append({'type': "FileRouingPathsFilePath",
                       'value': os.path.join(
                           json_folder, "routing_paths.json")})
        inputs.append({'type': "FileConstraintsFilePath",
                       'value': os.path.join(
                           json_folder, "constraints.json")})

        # execute mapping process
        self._pacman_exeuctor.execute_mapping(inputs)

        # sort out outputs datas
        self._placements = self._pacman_exeuctor.get_item("MemoryPlacements")
        self._router_tables = \
            self._pacman_exeuctor.get_item("MemoryRoutingTables")
        self._routing_infos = \
            self._pacman_exeuctor.get_item("MemoryRoutingInfos")
        self._tags = self._pacman_exeuctor.get_item("MemoryTags")
        self._graph_mapper = self._pacman_exeuctor.get_item("MemoryGraphMapper")
        self._partitioned_graph = \
            self._pacman_exeuctor.get_item("MemoryPartitionedGraph")

    def run(self, run_time):
        """

        :param run_time:
        :return:
        """
        # sort out config param to be valid types
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

        self.setup_interfaces(
            hostname=self._hostname,
            bmp_details=config.get("Machine", "bmp_names"),
            downed_chips=config.get("Machine", "down_chips"),
            downed_cores=config.get("Machine", "down_cores"),
            board_version=config.getint("Machine", "version"),
            number_of_boards=number_of_boards, width=width, height=height,
            is_virtual=config.getboolean("Machine", "virtual_board"),
            virtual_has_wrap_arounds=config.getboolean(
                "Machine", "requires_wrap_arounds"),
            auto_detect_bmp=config.getboolean("Machine", "auto_detect_bmp"),
            enable_reinjection=config.getboolean(
                "Machine", "enable_reinjection"))

        # adds extra stuff needed by the reload script which cannot be given
        # directly.
        if self._reports_states.transciever_report:
            self._reload_script.runtime = run_time
            self._reload_script.time_scale_factor = self._time_scale_factor

        # create network report if needed
        if self._reports_states is not None:
            reports.network_specification_partitionable_report(
                self._report_default_directory, self._partitionable_graph,
                self._hostname)

        # calculate number of machine time steps
        if run_time is not None:
            self._no_machine_time_steps =\
                int((run_time * 1000.0) / self._machine_time_step)
            ceiled_machine_time_steps = \
                math.ceil((run_time * 1000.0) / self._machine_time_step)
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
            logger.warn("You have set a runtime that will never end, this may"
                        "cause the neural models to fail to partition "
                        "correctly")
            for vertex in self._partitionable_graph.vertices:
                if (isinstance(vertex, AbstractPopulationRecordableVertex) and
                        vertex.record):
                    raise common_exceptions.ConfigurationException(
                        "recording a population when set to infinite runtime "
                        "is not currently supportable in this tool chain."
                        "watch this space")

        do_timing = config.getboolean("Reports", "outputTimesForSections")
        if do_timing:
            timer = Timer()
        else:
            timer = None

        self.set_runtime(run_time)
        logger.info("*** Running Mapper *** ")
        if do_timing:
            timer.start_timing()

        self.do_mapping(do_timing)

        # take timing measurements
        if do_timing:
            logger.info("Time to map model: {}".format(timer.take_sample()))

        # add database generation if requested
        needs_database = self._auto_detect_database(self._partitioned_graph)
        user_create_database = config.get("Database", "create_database")
        if ((user_create_database == "None" and needs_database) or
                user_create_database == "True"):

            database_progress = ProgressBar(10, "Creating database")

            wait_on_confirmation = config.getboolean(
                "Database", "wait_on_confirmation")
            self._database_interface = SpynnakerDataBaseWriter(
                self._app_data_runtime_folder, wait_on_confirmation,
                self._database_socket_addresses)

            self._database_interface.add_system_params(
                self._time_scale_factor, self._machine_time_step,
                self._runtime)
            database_progress.update()
            self._database_interface.add_machine_objects(self._machine)
            database_progress.update()
            self._database_interface.add_partitionable_vertices(
                self._partitionable_graph)
            database_progress.update()
            self._database_interface.add_partitioned_vertices(
                self._partitioned_graph, self._graph_mapper,
                self._partitionable_graph)
            database_progress.update()
            self._database_interface.add_placements(self._placements,
                                                    self._partitioned_graph)
            database_progress.update()
            self._database_interface.add_routing_infos(
                self._routing_infos, self._partitioned_graph)
            database_progress.update()
            self._database_interface.add_routing_tables(self._router_tables)
            database_progress.update()
            self._database_interface.add_tags(self._partitioned_graph,
                                              self._tags)
            database_progress.update()
            execute_mapping = config.getboolean(
                "Database", "create_routing_info_to_neuron_id_mapping")
            if execute_mapping:
                self._database_interface.create_atom_to_event_id_mapping(
                    graph_mapper=self._graph_mapper,
                    partitionable_graph=self._partitionable_graph,
                    partitioned_graph=self._partitioned_graph,
                    routing_infos=self._routing_infos)
            database_progress.update()
            # if using a reload script, add if that needs to wait for
            # confirmation
            if self._reports_states.transciever_report:
                self._reload_script.wait_on_confirmation = wait_on_confirmation
                for socket_address in self._database_socket_addresses:
                    self._reload_script.add_socket_address(socket_address)
            database_progress.update()
            database_progress.end()
            self._database_interface.send_read_notification()

        # execute data spec generation
        if do_timing:
            timer.start_timing()
        logger.info("*** Generating Output *** ")
        logger.debug("")
        executable_targets = self.generate_data_specifications()
        if do_timing:
            logger.info("Time to generate data: {}".format(
                timer.take_sample()))

        # execute data spec execution
        if do_timing:
            timer.start_timing()
        processor_to_app_data_base_address = \
            self.execute_data_specification_execution(
                config.getboolean("SpecExecution", "specExecOnHost"),
                self._hostname, self._placements, self._graph_mapper,
                write_text_specs=config.getboolean(
                    "Reports", "writeTextSpecs"),
                runtime_application_data_folder=self._app_data_runtime_folder,
                machine=self._machine)

        if self._reports_states is not None:
            reports.write_memory_map_report(self._report_default_directory,
                                            processor_to_app_data_base_address)

        if do_timing:
            logger.info("Time to execute data specifications: {}".format(
                timer.take_sample()))

        if (not isinstance(self._machine, VirtualMachine) and
                config.getboolean("Execute", "run_simulation")):
            if do_timing:
                timer.start_timing()

            logger.info("*** Loading tags ***")
            self.load_tags(self._tags)

            if self._do_load is True:
                logger.info("*** Loading data ***")
                self._load_application_data(
                    self._placements, self._graph_mapper,
                    processor_to_app_data_base_address, self._hostname,
                    app_data_folder=self._app_data_runtime_folder,
                    verify=config.getboolean("Mode", "verify_writes"))
                self.load_routing_tables(self._router_tables, self._app_id)
                logger.info("*** Loading executables ***")
                self.load_executable_images(executable_targets, self._app_id)
                logger.info("*** Loading buffers ***")
                self.set_up_send_buffering(self._partitioned_graph,
                                           self._placements, self._tags)

            # end of entire loading setup
            if do_timing:
                logger.debug("Time to load: {}".format(timer.take_sample()))

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                if do_timing:
                    timer.start_timing()
                # every thing is in sync0. load the initial buffers
                self._send_buffer_manager.load_initial_buffers()
                if do_timing:
                    logger.debug("Time to load buffers: {}".format(
                        timer.take_sample()))

                wait_on_confirmation = config.getboolean(
                    "Database", "wait_on_confirmation")
                send_start_notification = config.getboolean(
                    "Database", "send_start_notification")

                self.wait_for_cores_to_be_ready(executable_targets,
                                                self._app_id)

                # wait till external app is ready for us to start if required
                if (self._database_interface is not None and
                        wait_on_confirmation):
                    self._database_interface.wait_for_confirmation()

                self.start_all_cores(executable_targets, self._app_id)

                if (self._database_interface is not None and
                        send_start_notification):
                    self._database_interface.send_start_notification()

                if self._runtime is None:
                    logger.info("Application is set to run forever - exiting")
                else:
                    self.wait_for_execution_to_complete(
                        executable_targets, self._app_id, self._runtime,
                        self._time_scale_factor)
                self._has_ran = True
                if self._retrieve_provance_data:

                    progress = ProgressBar(self._placements.n_placements + 2,
                                           "Getting provenance data")

                    # retrieve provence data from central
                    file_path = os.path.join(self._report_default_directory,
                                             "provance_data")

                    # check the directory doesnt already exist
                    if not os.path.exists(file_path):
                        os.mkdir(file_path)

                    # write provanence data
                    self.write_provenance_data_in_xml(file_path, self._txrx)
                    progress.update()

                    pacman_executor_file_path = os.path.join(
                        file_path, "PACMAN_provancence_data.xml")
                    self._pacman_exeuctor.write_provenance_data_in_xml(
                        pacman_executor_file_path, self._txrx)

                    # retrieve provenance data from any cores that provide data
                    for placement in self._placements.placements:
                        if isinstance(placement.subvertex,
                                      AbstractProvidesProvenanceData):
                            core_file_path = os.path.join(
                                file_path,
                                "Provanence_data_for_{}_{}_{}_{}.xml".format(
                                    placement.subvertex.label,
                                    placement.x, placement.y, placement.p))
                            placement.subvertex.write_provenance_data_in_xml(
                                core_file_path, self.transceiver, placement)
                        progress.update()
                    progress.end()

        elif isinstance(self._machine, VirtualMachine):
            logger.info(
                "*** Using a Virtual Machine so no simulation will occur")
        else:
            logger.info("*** No simulation requested: Stopping. ***")

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
            return float(self._runtime)
        return 0.0

    def __repr__(self):
        return "Spinnaker object for machine {}".format(self._hostname)

    def generate_data_specifications(self):
        """ generates the dsg for the graph.

        :return:
        """

        # iterate though subvertexes and call generate_data_spec for each
        # vertex
        executable_targets = ExecutableTargets()

        # create a progress bar for end users
        progress_bar = ProgressBar(len(list(self._placements.placements)),
                                   "Generating data specifications")
        for placement in self._placements.placements:
            associated_vertex =\
                self._graph_mapper.get_vertex_from_subvertex(
                    placement.subvertex)

            # if the vertex can generate a DSG, call it
            if isinstance(associated_vertex, AbstractDataSpecableVertex):

                ip_tags = self._tags.get_ip_tags_for_vertex(
                    placement.subvertex)
                reverse_ip_tags = self._tags.get_reverse_ip_tags_for_vertex(
                    placement.subvertex)
                associated_vertex.generate_data_spec(
                    placement.subvertex, placement, self._partitioned_graph,
                    self._partitionable_graph, self._routing_infos,
                    self._hostname, self._graph_mapper,
                    self._report_default_directory, ip_tags, reverse_ip_tags,
                    self._write_text_specs, self._app_data_runtime_folder)

                # Get name of binary from vertex
                binary_name = associated_vertex.get_binary_file_name()

                # Attempt to find this within search paths
                binary_path = executable_finder.get_executable_path(
                    binary_name)
                if binary_path is None:
                    raise exceptions.ExecutableNotFoundException(binary_name)

                if not executable_targets.has_binary(binary_path):
                    executable_targets.add_binary(binary_path)
                executable_targets.add_processor(
                    binary_path, placement.x, placement.y, placement.p)

            progress_bar.update()

        # finish the progress bar
        progress_bar.end()

        return executable_targets

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

        if turn_off_machine is None:
            turn_off_machine = config.getboolean("Machine", "turn_off_machine")

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

        # execute app stop
        # self._txrx.stop_application(self._app_id)
        if self._create_database:
            self._database_interface.stop()

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

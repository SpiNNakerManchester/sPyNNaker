# pacman imports
from pacman.operations.router_check_functionality.valid_routes_checker import \
    ValidRouteChecker
from pacman.utilities import reports as pacman_reports
from pacman.operations.partition_algorithms.basic_partitioner import \
    BasicPartitioner
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.operations.tag_allocator_algorithms.basic_tag_allocator \
    import BasicTagAllocator
from pacman.model.routing_info.dict_based_partitioned_edge_n_keys_map \
    import DictBasedPartitionedEdgeNKeysMap
from pacman.operations.router_algorithms.basic_dijkstra_routing \
    import BasicDijkstraRouting
from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.operations.routing_info_allocator_algorithms.\
    basic_routing_info_allocator import BasicRoutingInfoAllocator
from pacman.utilities.progress_bar import ProgressBar

# spinnmachine imports
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router as MachineRouter
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.chip import Chip
from spinn_machine.virutal_machine import VirtualMachine

# common front end imports
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utilities import reports
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.interface.front_end_common_interface_functions \
    import FrontEndCommonInterfaceFunctions
from spinn_front_end_common.interface.front_end_common_configuration_functions\
    import FrontEndCommonConfigurationFunctions
from spinn_front_end_common.utilities.timer import Timer
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.interface.data_generator_interface import \
    DataGeneratorInterface
from spinn_front_end_common.interface.executable_finder import ExecutableFinder
from spinn_front_end_common.abstract_models.abstract_provides_n_keys_for_edge \
    import AbstractProvidesNKeysForEdge
from spinn_front_end_common.abstract_models.\
    abstract_provides_outgoing_edge_constraints \
    import AbstractProvidesOutgoingEdgeConstraints
from spinn_front_end_common.abstract_models.\
    abstract_provides_incoming_edge_constraints \
    import AbstractProvidesIncomingEdgeConstraints

# local front end imports
from spynnaker.pyNN.utilities.database.socket_address import SocketAddress
from spynnaker.pyNN.utilities.database.data_base_interface \
    import DataBaseInterface
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN.overridden_pacman_functions.graph_edge_filter \
    import GraphEdgeFilter
from spynnaker.pyNN.spynnaker_configurations import \
    SpynnakerConfigurationFunctions
from spynnaker.pyNN.utilities.conf import config
from spynnaker.pyNN import exceptions
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.models.abstract_models.abstract_virtual_vertex import \
    AbstractVirtualVertex
from spynnaker.pyNN.models.abstract_models\
    .abstract_send_me_multicast_commands_vertex \
    import AbstractSendMeMulticastCommandsVertex
from spynnaker.pyNN.models.abstract_models\
    .abstract_vertex_with_dependent_vertices \
    import AbstractVertexWithEdgeToDependentVertices
from spynnaker.pyNN.buffer_management.buffer_manager import BufferManager
from spynnaker.pyNN.models.abstract_models.buffer_models\
    .abstract_sends_buffers_from_host_partitioned_vertex\
    import AbstractSendsBuffersFromHostPartitionedVertex

# spinnman imports
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset

import logging
import math
import os
import sys
from multiprocessing.pool import ThreadPool

logger = logging.getLogger(__name__)

executable_finder = ExecutableFinder()


class Spinnaker(FrontEndCommonConfigurationFunctions,
                FrontEndCommonInterfaceFunctions,
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

        # database objects
        self._create_database = config.getboolean(
            "Database", "create_database")

        if database_socket_addresses is None:
            database_socket_addresses = list()
            listen_port = config.getint("Database", "listen_port")
            notify_port = config.getint("Database", "notify_port")
            noftiy_hostname = config.get("Database", "notify_hostname")
            database_socket_addresses.append(
                SocketAddress(noftiy_hostname, notify_port, listen_port))
        self._database_socket_addresses = database_socket_addresses
        self._database_interface = None

        if self._app_id is None:
            self._set_up_main_objects(
                app_id=config.getint("Machine", "appID"),
                execute_data_spec_report=config.getboolean(
                    "Reports", "writeTextSpecs"),
                execute_partitioner_report=config.getboolean(
                    "Reports", "writePartitionerReports"),
                execute_placer_report=config.getboolean(
                    "Reports", "writePlacerReports"),
                execute_router_dat_based_report=config.getboolean(
                    "Reports", "writeRouterDatReport"),
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
                in_debug_mode=config.get("Mode", "mode") == "Debug",
                generate_tag_report=config.getboolean(
                    "Reports", "writeTagAllocationReports"))

            self._set_up_pacman_algorthms_listings(
                partitioner_algorithm=config.get("Partitioner", "algorithm"),
                placer_algorithm=config.get("Placer", "algorithm"),
                key_allocator_algorithm=config.get(
                    "KeyAllocator", "algorithm"),
                routing_algorithm=config.get("Routing", "algorithm"))

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
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)
        self._spikes_per_second = float(config.getfloat(
            "Simulation", "spikes_per_second"))
        self._ring_buffer_sigma = float(config.getfloat(
            "Simulation", "ring_buffer_sigma"))

        FrontEndCommonInterfaceFunctions.__init__(
            self, self._reports_states, self._report_default_directory)

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

    def run(self, run_time):
        """

        :param run_time:
        :return:
        """
        self._setup_interfaces(
            hostname=self._hostname,
            virtual_x_dimension=config.getint("Machine",
                                              "virtual_board_x_dimension"),
            virtual_y_dimension=config.getint("Machine",
                                              "virtual_board_y_dimension"),
            downed_chips=config.get("Machine", "down_chips"),
            downed_cores=config.get("Machine", "down_cores"),
            requires_virtual_board=config.getboolean("Machine",
                                                     "virtual_board"),
            requires_wrap_around=config.getboolean("Machine",
                                                   "requires_wrap_arounds"),
            machine_version=config.getint("Machine", "version"))

        # add database generation if requested
        if self._create_database:
            wait_on_confirmation = \
                config.getboolean("Database", "wait_on_confirmation")
            self._database_interface = DataBaseInterface(
                self._app_data_runtime_folder, wait_on_confirmation,
                self._database_socket_addresses)

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
                if vertex.is_set_to_record_spikes():
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
        self.map_model()
        if do_timing:
            timer.take_sample()

        # load database if needed
        if self._create_database:
            self._database_interface.add_system_params(
                self._time_scale_factor, self._machine_time_step,
                self._runtime)
            self._database_interface.add_machine_objects(self._machine)
            self._database_interface.add_partitionable_vertices(
                self._partitionable_graph)
            self._database_interface.add_partitioned_vertices(
                self._partitioned_graph, self._graph_mapper,
                self._partitionable_graph)
            self._database_interface.add_placements(self._placements,
                                                    self._partitioned_graph)
            self._database_interface.add_routing_infos(
                self._routing_infos, self._partitioned_graph)
            self._database_interface.add_routing_tables(self._router_tables)
            self._database_interface.add_tags(self._partitioned_graph,
                                              self._tags)
            execute_mapping = config.getboolean(
                "Database", "create_routing_info_to_neuron_id_mapping")
            if execute_mapping:
                self._database_interface.create_neuron_to_key_mapping(
                    graph_mapper=self._graph_mapper,
                    partitionable_graph=self._partitionable_graph,
                    partitioned_graph=self._partitioned_graph,
                    routing_infos=self._routing_infos)
            self._database_interface.send_read_notification()

        # execute data spec generation
        if do_timing:
            timer.start_timing()
        logger.info("*** Generating Output *** ")
        logger.debug("")
        executable_targets = self.generate_data_specifications()
        if do_timing:
            timer.take_sample()

        # execute data spec execution
        if do_timing:
            timer.start_timing()
        processor_to_app_data_base_address = \
            self.execute_data_specification_execution(
                config.getboolean("SpecExecution", "specExecOnHost"),
                self._hostname, self._placements, self._graph_mapper,
                write_text_specs=config.getboolean(
                    "Reports", "writeTextSpecs"),
                runtime_application_data_folder=self._app_data_runtime_folder)

        if self._reports_states is not None:
            reports.write_memory_map_report(self._report_default_directory,
                                            processor_to_app_data_base_address)

        if do_timing:
            timer.take_sample()

        if (not isinstance(self._machine, VirtualMachine) and
                config.getboolean("Execute", "run_simulation")):
            if do_timing:
                timer.start_timing()

            logger.info("*** Loading tags ***")
            self._load_tags(self._tags)

            if self._do_load is True:
                logger.info("*** Loading data ***")
                self._load_application_data(
                    self._placements, self._router_tables, self._graph_mapper,
                    processor_to_app_data_base_address, self._hostname,
                    self._app_id,
                    machine_version=config.getint("Machine", "version"),
                    app_data_folder=self._app_data_runtime_folder)
                logger.info("*** Loading executables ***")
                self._load_executable_images(
                    executable_targets, self._app_id,
                    app_data_folder=self._app_data_runtime_folder)
                logger.info("*** Loading buffers ***")
                self._set_up_send_buffering()

            # end of entire loading setup
            if do_timing:
                timer.take_sample()

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                if self._reports_states.transciever_report:
                    reports.re_load_script_running_aspects(
                        self._app_data_runtime_folder, executable_targets,
                        self._hostname, self._app_id, run_time)

                # every thing is in sync0. load the initial buffers
                self._send_buffer_manager.load_initial_buffers()

                wait_on_confirmation = config.getboolean(
                    "Database", "wait_on_confirmation")
                send_start_notification = config.getboolean(
                    "Database", "send_start_notification")

                self._wait_for_cores_to_be_ready(executable_targets,
                                                 self._app_id)

                # wait till external app is ready for us to start if required
                if (self._database_interface is not None and
                        wait_on_confirmation):
                    logger.info(
                        "*** Awaiting for a response from an external source "
                        "to state its ready for the simulation to start ***")
                    self._database_interface.wait_for_confirmation()

                self._start_all_cores(executable_targets, self._app_id)

                if (self._database_interface is not None and
                        send_start_notification):
                    self._database_interface.send_start_notification()

                if self._runtime is None:
                    logger.info("Application is set to run forever - exiting")
                else:
                    self._wait_for_execution_to_complete(
                        executable_targets, self._app_id, self._runtime,
                        self._time_scale_factor)
                self._has_ran = True
                if self._retrieve_provance_data:

                    # retrieve provenance data
                    self._retieve_provance_data_from_machine(
                        executable_targets, self._router_tables, self._machine)
        elif isinstance(self._machine, VirtualMachine):
            logger.info(
                "*** Using a Virtual Machine so no simulation will occur")
        else:
            logger.info("*** No simulation requested: Stopping. ***")

    def _set_up_send_buffering(self):
        progress_bar = ProgressBar(
            len(self.partitioned_graph.subvertices),
            "on initialising the buffer managers for vertices which require"
            " buffering")

        # Create the buffer manager
        self._send_buffer_manager = BufferManager(
            self._placements, self._routing_infos, self._tags, self._txrx)

        for partitioned_vertex in self.partitioned_graph.subvertices:
            if isinstance(partitioned_vertex,
                          AbstractSendsBuffersFromHostPartitionedVertex):

                # Add the vertex to the managed vertices
                self._send_buffer_manager.add_sender_vertex(
                    partitioned_vertex)
            progress_bar.update()
        progress_bar.end()

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

    def map_model(self):
        """
        executes the pacman compilation stack
        """
        pacman_report_state = \
            self._reports_states.generate_pacman_report_states()

        self._add_virtual_chips()

        # execute partitioner
        self._execute_partitioner(pacman_report_state)

        # execute placer
        self._execute_placer(pacman_report_state)

        # exeucte tag allocator
        self._execute_tag_allocator(pacman_report_state)

        # execute pynn subedge pruning
        self._partitioned_graph, self._graph_mapper = \
            GraphEdgeFilter(self._report_default_directory)\
            .run(self._partitioned_graph, self._graph_mapper)

        # execute key allocator
        self._execute_key_allocator(pacman_report_state)

        # execute router
        self._execute_router(pacman_report_state)

    def _execute_tag_allocator(self, pacman_report_state):
        """

        :param pacman_report_state:
        :return:
        """
        if self._tag_allocator_algorithm is None:
            self._tag_allocator_algorithm = BasicTagAllocator()
        else:
            self._tag_allocator_algorithm = self._tag_allocator_algorithm()

        # execute tag allocation
        self._tags = self._tag_allocator_algorithm.allocate_tags(
            self._machine, self._placements)

        # generate reports
        if (pacman_report_state is not None and
                pacman_report_state.tag_allocation_report):
            pacman_reports.tag_allocator_report(
                self._report_default_directory, self._tags)

    def _execute_key_allocator(self, pacman_report_state):
        """ executes the key allocator

        :param pacman_report_state:
        :return:
        """
        if self._key_allocator_algorithm is None:
            self._key_allocator_algorithm = BasicRoutingInfoAllocator()
        else:
            self._key_allocator_algorithm = self._key_allocator_algorithm()

        # execute routing info generator
        # Generate an n_keys map for the graph and add constraints
        n_keys_map = DictBasedPartitionedEdgeNKeysMap()
        for edge in self._partitioned_graph.subedges:
            vertex_slice = self._graph_mapper.get_subvertex_slice(
                edge.pre_subvertex)
            super_edge = (self._graph_mapper
                          .get_partitionable_edge_from_partitioned_edge(edge))

            if not isinstance(super_edge.pre_vertex,
                              AbstractProvidesNKeysForEdge):
                n_keys_map.set_n_keys_for_patitioned_edge(edge,
                                                          vertex_slice.n_atoms)
            else:
                n_keys_map.set_n_keys_for_patitioned_edge(
                    edge,
                    super_edge.pre_vertex.get_n_keys_for_partitioned_edge(
                        edge, self._graph_mapper))

            if isinstance(super_edge.pre_vertex,
                          AbstractProvidesOutgoingEdgeConstraints):
                edge.add_constraints(
                    super_edge.pre_vertex.get_outgoing_edge_constraints(
                        edge, self._graph_mapper))
            if isinstance(super_edge.post_vertex,
                          AbstractProvidesIncomingEdgeConstraints):
                edge.add_constraints(
                    super_edge.post_vertex.get_incoming_edge_constraints(
                        edge, self._graph_mapper))

        # execute routing info generator
        self._routing_infos = \
            self._key_allocator_algorithm.allocate_routing_info(
                self._partitioned_graph, self._placements, n_keys_map)

        # generate reports
        if (pacman_report_state is not None and
                pacman_report_state.routing_info_report):
            pacman_reports.routing_info_reports(
                self._report_default_directory, self._partitioned_graph,
                self._routing_infos)

    def _execute_router(self, pacman_report_state):
        """ exectes the router algorithum

        :param pacman_report_state:
        :return:
        """

        # set up a default placer algorithm if none are specified
        if self._router_algorithm is None:
            self._router_algorithm = BasicDijkstraRouting()
        else:
            self._router_algorithm = self._router_algorithm()

        self._router_tables = \
            self._router_algorithm.route(
                self._routing_infos, self._placements, self._machine,
                self._partitioned_graph)

        if pacman_report_state is not None and \
                pacman_report_state.router_report:
            pacman_reports.router_reports(
                graph=self._partitionable_graph, hostname=self._hostname,
                graph_to_sub_graph_mapper=self._graph_mapper,
                placements=self._placements,
                report_folder=self._report_default_directory,
                include_dat_based=pacman_report_state.router_dat_based_report,
                routing_tables=self._router_tables,
                routing_info=self._routing_infos, machine=self._machine)

        if self._in_debug_mode:

            # check that all routes are valid and no cycles exist
            valid_route_checker = ValidRouteChecker(
                placements=self._placements, routing_infos=self._routing_infos,
                routing_tables=self._router_tables, machine=self._machine,
                partitioned_graph=self._partitioned_graph)
            valid_route_checker.validate_routes()

    def _execute_partitioner(self, pacman_report_state):
        """ executes the partitioner function

        :param pacman_report_state:
        :return:
        """

        # execute partitioner or default partitioner (as seen fit)
        if self._partitioner_algorithm is None:
            self._partitioner_algorithm = BasicPartitioner()
        else:
            self._partitioner_algorithm = self._partitioner_algorithm()

        # execute partitioner
        self._partitioned_graph, self._graph_mapper = \
            self._partitioner_algorithm.partition(self._partitionable_graph,
                                                  self._machine)

        # execute reports
        if (pacman_report_state is not None and
                pacman_report_state.partitioner_report):
            pacman_reports.partitioner_reports(
                self._report_default_directory, self._hostname,
                self._partitionable_graph, self._graph_mapper)

    def _execute_placer(self, pacman_report_state):
        """ executes the placer

        :param pacman_report_state:
        :return:
        """

        # execute placer or default placer (as seen fit)
        if self._placer_algorithm is None:
            self._placer_algorithm = BasicPlacer()
        else:
            self._placer_algorithm = self._placer_algorithm()

        # execute placer
        self._placements = self._placer_algorithm.place(
            self._partitioned_graph, self._machine)

        # execute placer reports if needed
        if (pacman_report_state is not None and
                pacman_report_state.placer_report):
            pacman_reports.placer_reports_with_partitionable_graph(
                graph=self._partitionable_graph,
                graph_mapper=self._graph_mapper, hostname=self._hostname,
                machine=self._machine, placements=self._placements,
                report_folder=self._report_default_directory)

    def generate_data_specifications(self):
        """ generates the dsg for the graph.

        :return:
        """

        # iterate though subvertexes and call generate_data_spec for each
        # vertex
        executable_targets = dict()
        no_processors = config.getint("Threading", "dsg_threads")
        thread_pool = ThreadPool(processes=no_processors)

        # create a progress bar for end users
        progress_bar = ProgressBar(len(list(self._placements.placements)),
                                   "on generating data specifications")
        data_generator_interfaces = list()
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
                data_generator_interface = DataGeneratorInterface(
                    associated_vertex, placement.subvertex, placement,
                    self._partitioned_graph, self._partitionable_graph,
                    self._routing_infos, self._hostname, self._graph_mapper,
                    self._report_default_directory, ip_tags, reverse_ip_tags,
                    self._writeTextSpecs, self._app_data_runtime_folder,
                    progress_bar)
                data_generator_interfaces.append(data_generator_interface)
                thread_pool.apply_async(data_generator_interface.start)

                # Get name of binary from vertex
                binary_name = associated_vertex.get_binary_file_name()

                # Attempt to find this within search paths
                binary_path = executable_finder.get_executable_path(
                    binary_name)
                if binary_path is None:
                    raise exceptions.ExecutableNotFoundException(binary_name)

                if binary_path in executable_targets:
                    executable_targets[binary_path].add_processor(placement.x,
                                                                  placement.y,
                                                                  placement.p)
                else:
                    processors = [placement.p]
                    initial_core_subset = CoreSubset(placement.x, placement.y,
                                                     processors)
                    list_of_core_subsets = [initial_core_subset]
                    executable_targets[binary_path] = \
                        CoreSubsets(list_of_core_subsets)

        for data_generator_interface in data_generator_interfaces:
            data_generator_interface.wait_for_finish()
        thread_pool.close()
        thread_pool.join()

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

    def add_edge(self, edge_to_add):
        """

        :param edge_to_add:
        :return:
        """
        self._partitionable_graph.add_edge(edge_to_add)

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
            timescale_factor=self._time_scale_factor)

    def _add_virtual_chips(self):
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractVirtualVertex):

                # check if the virtual chip doesn't already exist
                if self._machine.get_chip_at(vertex.virtual_chip_x,
                                             vertex.virtual_chip_y) is None:
                    virutal_chip = self._create_virtual_chip(vertex)
                    self._machine.add_chip(virutal_chip)

    def _create_virtual_chip(self, virtual_vertex):
        sdram_object = SDRAM()

        # creates the two links
        virtual_link_id = (virtual_vertex
                           .connected_to_real_chip_link_id + 3) % 6
        to_virtual_chip_link = Link(
            destination_x=virtual_vertex.virtual_chip_x,
            destination_y=virtual_vertex.virtual_chip_y,
            source_x=virtual_vertex.connected_to_real_chip_x,
            source_y=virtual_vertex.connected_to_real_chip_y,
            multicast_default_from=virtual_link_id,
            multicast_default_to=virtual_link_id,
            source_link_id=virtual_vertex.connected_to_real_chip_link_id)

        from_virtual_chip_link = Link(
            destination_x=virtual_vertex.connected_to_real_chip_x,
            destination_y=virtual_vertex.connected_to_real_chip_y,
            source_x=virtual_vertex.virtual_chip_x,
            source_y=virtual_vertex.virtual_chip_y,
            multicast_default_from=(virtual_vertex
                                    .connected_to_real_chip_link_id),
            multicast_default_to=virtual_vertex.connected_to_real_chip_link_id,
            source_link_id=virtual_link_id)

        # create the router
        links = [from_virtual_chip_link]
        router_object = MachineRouter(
            links=links, emergency_routing_enabled=False,
            clock_speed=MachineRouter.ROUTER_DEFAULT_CLOCK_SPEED,
            n_available_multicast_entries=sys.maxint)

        # create the processors
        processors = list()
        for virtual_core_id in range(0, 128):
            processors.append(Processor(virtual_core_id,
                                        Processor.CPU_AVAILABLE,
                                        virtual_core_id == 0))

        # connect the real chip with the virtual one
        connected_chip = self._machine.get_chip_at(
            virtual_vertex.connected_to_real_chip_x,
            virtual_vertex.connected_to_real_chip_y)
        connected_chip.router.add_link(to_virtual_chip_link)

        # return new v chip
        return Chip(
            processors=processors, router=router_object, sdram=sdram_object,
            x=virtual_vertex.virtual_chip_x, y=virtual_vertex.virtual_chip_y,
            virtual=True, nearest_ethernet_x=None, nearest_ethernet_y=None)

    def stop(self, stop_on_board=True):
        """

        :param stop_on_board: boolean which decides if the board should have
        its router tables and tags cleared
        :return:
        """
        if stop_on_board:
            for ip_tag in self._tags.ip_tags:
                self._txrx.clear_ip_tag(
                    ip_tag.tag, board_address=ip_tag.board_address)
            for reverse_ip_tag in self._tags.reverse_ip_tags:
                self._txrx.clear_ip_tag(
                    reverse_ip_tag.tag,
                    board_address=reverse_ip_tag.board_address)

            # self._txrx.stop_application(self._app_id)
        if self._create_database:
            self._database_interface.stop()

        # stop the transciever
        self._txrx.close()

# pacman imports
from pacman.operations.router_check_functionality.valid_routes_checker import \
    ValidRouteChecker
from pacman.utilities import reports as pacman_reports
from pacman.operations.partition_algorithms.basic_partitioner import \
    BasicPartitioner
from spynnaker.pyNN.buffer_management.buffer_manager import BufferManager
from spynnaker.pyNN.models.abstract_models.buffer_models\
    .abstract_sends_buffers_from_host_partitioned_vertex\
    import AbstractSendsBuffersFromHostPartitionedVertex
from spynnaker.pyNN.models.abstract_models.abstract_virtual_vertex import \
    AbstractVirtualVertex
from spynnaker.pyNN.models.abstract_models.abstract_provides_n_keys_for_edge\
    import AbstractProvidesNKeysForEdge
from spynnaker.pyNN.models.abstract_models\
    .abstract_provides_outgoing_edge_constraints \
    import AbstractProvidesOutgoingEdgeConstraints
from spynnaker.pyNN.models.abstract_models\
    .abstract_provides_incoming_edge_constraints \
    import AbstractProvidesIncomingEdgeConstraints
from spynnaker.pyNN.models.abstract_models\
    .abstract_send_me_multicast_commands_vertex \
    import AbstractSendMeMulticastCommandsVertex
from spynnaker.pyNN.models.abstract_models\
    .abstract_vertex_with_dependent_vertices \
    import AbstractVertexWithEdgeToDependentVertices
from pacman.operations.tag_allocator_algorithms.basic_tag_allocator \
    import BasicTagAllocator
from pacman.model.partitionable_graph.abstract_partitionable_edge \
    import AbstractPartitionableEdge
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

# internal imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.utility_models.command_sender import CommandSender
from spynnaker.pyNN.spynnaker_comms_functions import SpynnakerCommsFunctions
from spynnaker.pyNN.spynnaker_configuration import SpynnakerConfiguration
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.database.data_base_interface \
    import DataBaseInterface
from spynnaker.pyNN.utilities.database.socket_address import SocketAddress
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import reports
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN.overridden_pacman_functions.graph_edge_filter \
    import GraphEdgeFilter
from spynnaker.pyNN.utilities.data_generator_interface import \
    DataGeneratorInterface

# spinnman imports
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset

import logging
import math
import os
import sys
from multiprocessing.pool import ThreadPool

logger = logging.getLogger(__name__)


class Spinnaker(SpynnakerConfiguration, SpynnakerCommsFunctions):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None, binary_search_paths=None,
                 database_socket_addresses=None):
        SpynnakerConfiguration.__init__(self, host_name, graph_label)

        if binary_search_paths is None:
            binary_search_paths = []

        if database_socket_addresses is None:
            database_socket_addresses = list()
            listen_port = conf.config.getint("Database", "listen_port")
            notify_port = conf.config.getint("Database", "notify_port")
            noftiy_hostname = conf.config.get("Database", "notify_hostname")
            database_socket_addresses.append(
                SocketAddress(noftiy_hostname, notify_port, listen_port))
        self._database_socket_addresses = database_socket_addresses

        if self._app_id is None:
            self._set_up_main_objects()
            self._set_up_pacman_algorthms_listings()
            self._set_up_executable_specifics()
            self._set_up_report_specifics()
            self._set_up_output_application_data_specifics()
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)
        self._spikes_per_second = float(conf.config.getfloat(
            "Simulation", "spikes_per_second"))
        self._ring_buffer_sigma = float(conf.config.getfloat(
            "Simulation", "ring_buffer_sigma"))

        SpynnakerCommsFunctions.__init__(self, self._reports_states,
                                         self._report_default_directory)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

        # Begin list of binary search paths
        # With those passed to constructor
        self._binary_search_paths = binary_search_paths

        # Determine default executable folder location
        binary_path = os.path.abspath(exceptions.__file__)
        binary_path = os.path.abspath(os.path.join(binary_path, os.pardir))
        binary_path = os.path.join(binary_path, "model_binaries")

        # add this default to end of list of search paths
        self._binary_search_paths.append(binary_path)
        self._edge_count = 0

        # Manager of buffered sending
        self._send_buffer_manager = None

    def run(self, run_time):
        self._setup_interfaces(hostname=self._hostname)

        # add database generation if requested
        if self._create_database:
            wait_on_confirmation = \
                conf.config.getboolean("Database", "wait_on_confirmation")
            self._database_interface = DataBaseInterface(
                self._app_data_runtime_folder, wait_on_confirmation,
                self._database_socket_addresses)

        # create network report if needed
        if self._reports_states is not None:
            reports.network_specification_report(
                self._report_default_directory, self._partitionable_graph,
                self._hostname)

        # calculate number of machine time steps
        if run_time is not None:
            self._no_machine_time_steps =\
                int((run_time * 1000.0) / self._machine_time_step)
            ceiled_machine_time_steps = \
                math.ceil((run_time * 1000.0) / self._machine_time_step)
            if self._no_machine_time_steps != ceiled_machine_time_steps:
                raise exceptions.ConfigurationException(
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
                    raise exceptions.ConfigurationException(
                        "recording a population when set to infinite runtime "
                        "is not currently supportable in this tool chain."
                        "watch this space")

        do_timing = conf.config.getboolean("Reports", "outputTimesForSections")
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
            execute_mapping = conf.config.getboolean(
                "Database", "create_routing_info_to_neuron_id_mapping")
            if execute_mapping:
                self._database_interface.create_neuron_to_key_mapping(
                    graph_mapper=self._graph_mapper,
                    partitionable_graph=self._partitionable_graph,
                    partitioned_graph=self._partitioned_graph,
                    routing_infos=self._routing_infos,
                    placements=self._placements)
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
                conf.config.getboolean("SpecExecution", "specExecOnHost"),
                self._hostname, self._placements, self._graph_mapper)

        if self._reports_states is not None:
            reports.write_memory_map_report(self._report_default_directory,
                                            processor_to_app_data_base_address)

        if do_timing:
            timer.take_sample()

        if (not isinstance(self._machine, VirtualMachine) and
                conf.config.getboolean("Execute", "run_simulation")):
            if do_timing:
                timer.start_timing()

            logger.info("*** Loading tags ***")
            self._load_tags(self._tags)

            if self._do_load is True:
                logger.info("*** Loading data ***")
                self._load_application_data(
                    self._placements, self._router_tables, self._graph_mapper,
                    processor_to_app_data_base_address, self._hostname,
                    self._app_id)
                logger.info("*** Loading executables ***")
                self._load_executable_images(executable_targets, self._app_id)
                logger.info("*** Loading buffers ***")
                self._set_up_send_buffering()

            # end of entire loading setup
            if do_timing:
                timer.take_sample()

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                if self._reports_states.transciever_report:
                    binary_folder = conf.config.get("SpecGeneration",
                                                    "Binary_folder")
                    reports.re_load_script_running_aspects(
                        binary_folder, executable_targets, self._hostname,
                        self._app_id, run_time)

                # every thing is in sync0. load the initial buffers
                self._send_buffer_manager.load_initial_buffers()

                wait_on_confirmation = conf.config.getboolean(
                    "Database", "wait_on_confirmation")
                send_start_notification = conf.config.getboolean(
                    "Database", "send_start_notification")
                self._start_execution_on_machine(
                    executable_targets, self._app_id, self._runtime,
                    self._time_scale_factor, wait_on_confirmation,
                    send_start_notification, self._database_interface,
                    self._in_debug_mode)
                self._has_ran = True
                if self._retrieve_provance_data:

                    # retrieve provance data
                    self._retieve_provance_data_from_machine(
                        executable_targets, self._router_tables, self._machine)
        elif isinstance(self._machine, VirtualMachine):
            logger.info(
                "*** Using a Virtual Machine so no simulation will occur")
        else:
            logger.info("*** No simulation requested: Stopping. ***")

    def _set_up_send_buffering(self):
        progress_bar = ProgressBar(
            len(self.partitionable_graph.vertices),
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
        return self._app_id

    @property
    def has_ran(self):
        return self._has_ran

    @property
    def machine_time_step(self):
        return self._machine_time_step

    @property
    def no_machine_time_steps(self):
        return self._no_machine_time_steps

    @property
    def timescale_factor(self):
        return self._time_scale_factor

    @property
    def spikes_per_second(self):
        return self._spikes_per_second

    @property
    def ring_buffer_sigma(self):
        return self._ring_buffer_sigma

    @property
    def get_multi_cast_source(self):
        return self._multi_cast_vertex

    @property
    def partitioned_graph(self):
        return self._partitioned_graph

    @property
    def partitionable_graph(self):
        return self._partitionable_graph

    @property
    def placements(self):
        return self._placements

    @property
    def transceiver(self):
        return self._txrx

    @property
    def graph_mapper(self):
        return self._graph_mapper

    @property
    def routing_infos(self):
        return self._routing_infos

    def set_app_id(self, value):
        self._app_id = value

    def set_runtime(self, value):
        self._runtime = value

    def get_current_time(self):
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

        # Generate an n_keys map for the graph and add constraints
        n_keys_map = DictBasedPartitionedEdgeNKeysMap()
        for edge in self._partitioned_graph.subedges:
            vertex_slice = self._graph_mapper.get_subvertex_slice(
                edge.pre_subvertex)
            super_edge = (self._graph_mapper
                          .get_partitionable_edge_from_partitioned_edge(edge))
            if vertex_slice.n_atoms > 2048:
                raise exceptions.ConfigurationException(
                    "The current models can only support up to 2048 atoms"
                    " per core (restricted by the supported key format)")

            if not isinstance(super_edge.pre_vertex,
                              AbstractProvidesNKeysForEdge):
                n_keys_map.set_n_keys_for_patitioned_edge(edge,
                                                          vertex_slice.n_atoms)
            else:
                n_keys_map.set_n_keys_for_patitioned_edge(
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
            pacman_reports.placer_reports(
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
        no_processors = conf.config.getint("Threading", "dsg_threads")
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
                    progress_bar)
                data_generator_interfaces.append(data_generator_interface)
                thread_pool.apply_async(data_generator_interface.start)

                # Get name of binary from vertex
                binary_name = associated_vertex.get_binary_file_name()

                # Attempt to find this within search paths
                binary_path = self._get_executable_path(binary_name)
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
        if isinstance(vertex_to_add, CommandSender):
            self._multi_cast_vertex = vertex_to_add

        self._partitionable_graph.add_vertex(vertex_to_add)

        if isinstance(vertex_to_add, AbstractSendMeMulticastCommandsVertex):
            if self._multi_cast_vertex is None:
                self._multi_cast_vertex = CommandSender(
                    self._machine_time_step, self._time_scale_factor)
                self.add_vertex(self._multi_cast_vertex)
            edge = AbstractPartitionableEdge(
                self._multi_cast_vertex, vertex_to_add)
            self._multi_cast_vertex.add_commands(vertex_to_add.commands, edge)
            self.add_edge(edge)

        # add any dependent edges and verts if needed
        if isinstance(vertex_to_add,
                      AbstractVertexWithEdgeToDependentVertices):
            for dependant_vertex in vertex_to_add.dependent_vertices:
                self.add_vertex(dependant_vertex)
                dependant_edge = AbstractPartitionableEdge(
                    pre_vertex=vertex_to_add, post_vertex=dependant_vertex)
                self.add_edge(dependant_edge)

    def add_edge(self, edge_to_add):
        self._partitionable_graph.add_edge(edge_to_add)

    def create_population(self, size, cellclass, cellparams, structure, label):
        return Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, spinnaker=self)

    def create_projection(
            self, presynaptic_population, postsynaptic_population, connector,
            source, target, synapse_dynamics, label, rng):
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

    def _get_executable_path(self, executable_name):

        # Loop through search paths
        for path in self._binary_search_paths:
            # Rebuild filename
            potential_filename = os.path.join(path, executable_name)

            # If this filename exists, return it
            if os.path.isfile(potential_filename):
                return potential_filename

        # No executable found
        return None

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
        if stop_on_board:
            for router_table in self._router_tables.routing_tables:
                if (not self._machine.get_chip_at(router_table.x,
                                                  router_table.y).virtual and
                        len(router_table.multicast_routing_entries) > 0):
                    self._txrx.clear_router_diagnostic_counters(router_table.x,
                                                                router_table.y)

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

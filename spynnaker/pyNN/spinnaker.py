# pacman imports
from pacman.model.constraints.\
    vertex_requires_virtual_chip_in_machine_constraint import \
    VertexRequiresVirtualChipInMachineConstraint
from spynnaker.pyNN import model_binaries
import exceptions
from pacman.operations.router_check_functionality.valid_routes_checker import \
    ValidRouteChecker
from pacman.utilities import reports as pacman_reports
from pacman.operations.partition_algorithms.basic_partitioner import \
    BasicPartitioner
from pacman.operations.router_algorithms.basic_dijkstra_routing \
    import BasicDijkstraRouting
from pacman.operations.placer_algorithms.basic_placer import BasicPlacer
from pacman.operations.routing_info_allocator_algorithms.\
    basic_routing_info_allocator import BasicRoutingInfoAllocator
from pacman.utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls as pacman_utility_calls

# spinnmachine imports
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router as MachineRouter
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.chip import Chip

# common front end imports
from spinn_front_end_common.utilities import exceptions as common_exceptions, \
    reports
from spinn_front_end_common.abstract_models.abstract_iptagable_vertex import \
    AbstractIPTagableVertex
from spinn_front_end_common.abstract_models.abstract_reverse_iptagable_vertex \
    import AbstractReverseIPTagableVertex
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.interface.front_end_common_interface_functions \
    import FrontEndCommonInterfaceFunctions
from spinn_front_end_common.interface.front_end_common_configuration_functions \
    import FrontEndCommonConfigurationFunctions
from spinn_front_end_common.utilities.timer import Timer
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spinn_front_end_common.interface.data_generator_interface import \
    DataGeneratorInterface

# local front end imports
from spynnaker.pyNN.utilities.data_base_thread import DataBaseThread
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN.overridden_pacman_functions.graph_edge_filter \
    import GraphEdgeFilter
from spynnaker.pyNN.spynnaker_configurations import \
    SpynnakerConfigurationFunctions
from spynnaker.pyNN.utilities.conf import config

# spinnman imports
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset
from spinnman.model.iptag.reverse_iptag import ReverseIPTag

import logging
import math
import os
import sys
from multiprocessing.pool import ThreadPool

logger = logging.getLogger(__name__)


class Spinnaker(FrontEndCommonConfigurationFunctions,
                FrontEndCommonInterfaceFunctions,
                SpynnakerConfigurationFunctions):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None, binary_search_paths=[]):
        FrontEndCommonConfigurationFunctions.__init__(self, host_name,
                                                      graph_label)
        SpynnakerConfigurationFunctions.__init__(self)

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
                create_database=config.get("Database", "create_database"))

            self._set_up_pacman_algorthms_listings(
                partitioner_algorithm=config.get("Partitioner", "algorithm"),
                placer_algorithm=config.get("Placer", "algorithm"),
                key_allocator_algorithm=None,
                routing_algorithm=config.get("Routing", "algorithm"))

            # get the pynn specific key allocator algorithm
            #  (overloaded from common call)
            self._key_allocator_algorithm = \
                self.get_pynn_specific_key_allocator()
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
                    "Reports", "defaultApplicationDataFilePath")
            )
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

        # Begin list of binary search paths
        # With those passed to constructor
        self._binary_search_paths = binary_search_paths

        # Determine default executable folder location
        # and add this default to end of list of search paths
        self._binary_search_paths.append(os.path.dirname(
            model_binaries.__file__))
        self._edge_count = 0

    def run(self, run_time):
        self._setup_interfaces(
            hostname=self._hostname,
            virtual_x_dimension=config.get("Machine",
                                           "virutal_board_x_dimension"),
            virtual_y_dimension=config.get("Machine",
                                           "virutal_board_y_dimension"),
            downed_chips=config.get("Machine", "down_chips"),
            downed_cores=config.get("Machine", "down_cores"),
            requires_virtual_board=config.getboolean("Machine",
                                                     "virtual_board"),
            requires_wrap_around=config.get("Machine",
                                            "requires_wrap_arounds"),
            machine_version=config.getint("Machine", "version"))

        # add database generation if requested
        if self._create_database:
            execute_mapping = config.getboolean(
                "Database", "create_routing_info_to_neuron_id_mapping")
            wait_on_confirmation = \
                config.getboolean("Database", "wait_on_confirmation")
            self._database_thread = DataBaseThread(
                self._app_data_runtime_folder, execute_mapping,
                wait_on_confirmation)
            self._database_thread.start()

        # create network report if needed
        if self._reports_states is not None:
            reports.network_specification_report(
                self._report_default_directory, self._partitionable_graph,
                self._hostname)

        # calcualte number of machien time steps
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
                vertex.set_no_machine_time_steps(self._no_machine_time_steps)
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
            self._database_thread.add_system_params(
                self._time_scale_factor, self._machine_time_step,
                self._runtime)
            self._database_thread.add_machine_objects(self._machine)
            self._database_thread.add_partitionable_vertices(
                self._partitionable_graph)
            self._database_thread.add_partitioned_vertices(
                self._partitioned_graph, self._graph_mapper)
            self._database_thread.add_placements(self._placements)
            self._database_thread.add_routing_infos(self._routing_infos)
            self._database_thread.add_routing_tables(self._router_tables)

        # extract iptags required by the graph
        self._set_iptags()
        self._set_reverse_ip_tags()

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

        if config.getboolean("Execute", "run_simulation"):
            if do_timing:
                timer.start_timing()

            logger.info("*** Loading Iptags ***")
            self._load_iptags()
            logger.info("*** Loading Reverse Iptags***")
            self._load_reverse_ip_tags()

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
            if do_timing:
                timer.take_sample()

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                if self._reports_states.transciever_report:
                    reports.re_load_script_running_aspects(
                        self._app_data_runtime_folder, executable_targets,
                        self._hostname, self._app_id, run_time)

                wait_on_confirmation = \
                    config.getboolean("Database", "wait_on_confirmation")
                self._start_execution_on_machine(
                    executable_targets, self._app_id, self._runtime,
                    self._time_scale_factor, wait_on_confirmation,
                    self._database_thread, self._in_debug_mode)
                self._has_ran = True
                if self._retrieve_provance_data:
                    # retrieve provenance data
                    self._retieve_provance_data_from_machine(
                        executable_targets)
        else:
            logger.info("*** No simulation requested: Stopping. ***")

    def _set_iptags(self):
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractIPTagableVertex):
                iptag = vertex.get_ip_tag()
                if iptag.tag is not None:
                    if iptag.tag > self._current_max_tag_value:
                        self._current_max_tag_value = iptag.tag
                self._add_iptag(iptag)
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractIPTagableVertex):
                iptag = vertex.get_ip_tag()
                if iptag.tag is None:
                    iptag.set_tag(self._current_max_tag_value + 1)
                    vertex.set_tag(self._current_max_tag_value + 1)
                    self._current_max_tag_value += 1
                    self._add_iptag(iptag)

    def _set_reverse_ip_tags(self):
        # extract reverse iptags required by the graph
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractReverseIPTagableVertex):
                reverse_iptag = vertex.get_reverse_ip_tag()
                if reverse_iptag.tag is not None:
                    if reverse_iptag.tag > self._current_max_tag_value:
                        self._current_max_tag_value = reverse_iptag.tag
                    reverse_iptag = self._create_reverse_iptag_from_iptag(
                        reverse_iptag, vertex)
                    self._add_reverse_tag(reverse_iptag)
        for vertex in self._partitionable_graph.vertices:
            if isinstance(vertex, AbstractReverseIPTagableVertex):
                reverse_iptag = vertex.get_reverse_ip_tag()
                if reverse_iptag.tag is None:
                    reverse_iptag.set_tag(self._current_max_tag_value + 1)
                    vertex.set_reverse_iptag_tag(
                        self._current_max_tag_value + 1)
                    self._current_max_tag_value += 1
                    reverse_iptag = self._create_reverse_iptag_from_iptag(
                        reverse_iptag, vertex)
                    self._add_reverse_tag(reverse_iptag)

    def _create_reverse_iptag_from_iptag(self, reverse_iptag, vertex):
        subverts = self._graph_mapper.get_subvertices_from_vertex(vertex)
        if len(subverts) > 1:
            raise common_exceptions.ConfigurationException(
                "reverse iptaggable populations can only be supported if they"
                " are partitoned in a 1 to 1 ratio. Please reduce the number "
                "of neurons per core, or the max-atoms per core to support a "
                "one core mapping for your iptaggable population.")
        subvert = next(iter(subverts))
        placement = self._placements.get_placement_of_subvertex(subvert)
        return ReverseIPTag(
            port=reverse_iptag.port, tag=reverse_iptag.tag,
            destination_x=placement.x, destination_y=placement.y,
            destination_p=placement.p)

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

        self._check_if_theres_any_pre_placement_constraints_to_satisify()

        # execute partitioner
        self._execute_partitioner(pacman_report_state)

        # execute placer
        self._execute_placer(pacman_report_state)

        # execute pynn subedge pruning
        self._partitioned_graph, self._graph_mapper = \
            GraphEdgeFilter(self._report_default_directory)\
            .run(self._partitioned_graph, self._graph_mapper)

        # execute key allocator
        self._execute_key_allocator(pacman_report_state)

        # execute router
        self._execute_router(pacman_report_state)

    def _execute_key_allocator(self, pacman_report_state):
        if self._key_allocator_algorithm is None:
            self._key_allocator_algorithm = BasicRoutingInfoAllocator()
        else:
            self._key_allocator_algorithm = self._key_allocator_algorithm()

        # execute routing info generator
        self._routing_infos = \
            self._key_allocator_algorithm.allocate_routing_info(
                self._partitioned_graph, self._placements)

        # generate reports
        if (pacman_report_state is not None and
                pacman_report_state.routing_info_report):
            pacman_reports.routing_info_reports(
                self._report_default_directory, self._hostname,
                self._partitioned_graph, self._placements, self._routing_infos)

    def _execute_router(self, pacman_report_state):

        # set up a default placer algorithm if none are specified
        if self._router_algorithm is None:
            self._router_algorithm = BasicDijkstraRouting()
        else:
            self._router_algorithm = self._router_algorithm()

        self._router_tables = \
            self._router_algorithm.route(
                self._routing_infos, self._placements, self._machine,
                self._partitioned_graph)

        if self._in_debug_mode:
            # check that all routes are valid and no cycles exist
            valid_route_checker = ValidRouteChecker(
                placements=self._placements, routing_infos=self._routing_infos,
                routing_tables=self._router_tables, machine=self._machine,
                partitioned_graph=self._partitioned_graph)
            valid_route_checker.validate_routes()

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

    def _execute_partitioner(self, pacman_report_state):

        # execute partitioner or default partitioner (as seen fit)
        if self._partitioner_algorithm is None:
            self._partitioner_algorithm = \
                BasicPartitioner(self._machine_time_step,
                                 self._no_machine_time_steps)
        else:
            self._partitioner_algorithm = \
                self._partitioner_algorithm(self._machine_time_step,
                                            self._no_machine_time_steps)

        # if algorithm needs a placer, add placer algorithm
        if hasattr(self._partitioner_algorithm, "set_placer_algorithm"):
            self._partitioner_algorithm.set_placer_algorithm(
                self._placer_algorithm, self._machine)

        self._partitioned_graph, self._graph_mapper = \
            self._partitioner_algorithm.partition(self._partitionable_graph,
                                                  self._machine)

        if (pacman_report_state is not None and
                pacman_report_state.partitioner_report):
            pacman_reports.partitioner_reports(
                self._report_default_directory, self._hostname,
                self._partitionable_graph, self._graph_mapper)

    def _execute_placer(self, pacman_report_state):

        # execute placer or default placer (as seen fit)
        if self._placer_algorithm is None:
            self._placer_algorithm = BasicPlacer(self._machine)
        else:
            self._placer_algorithm = self._placer_algorithm(self._machine)
        self._placements = self._placer_algorithm.place(
            self._partitioned_graph)

        # execute placer reports if needed
        if (pacman_report_state is not None and
                pacman_report_state.placer_report):
            pacman_reports.placer_reports(
                graph=self._partitionable_graph,
                graph_mapper=self._graph_mapper, hostname=self._hostname,
                machine=self._machine, placements=self._placements,
                report_folder=self._report_default_directory)

    def generate_data_specifications(self):
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
                data_generator_interface = DataGeneratorInterface(
                    associated_vertex, placement.subvertex, placement,
                    self._partitioned_graph, self._partitionable_graph,
                    self._routing_infos, self._hostname, self._graph_mapper,
                    self._report_default_directory,
                    config.getboolean("Reports", "writeTextSpecs"),
                    self._app_data_runtime_folder, progress_bar)
                data_generator_interfaces.append(data_generator_interface)
                thread_pool.apply_async(data_generator_interface.start())

                # Get name of binary from vertex
                binary_name = associated_vertex.get_binary_file_name()

                # Attempt to find this within search paths
                binary_path = self._get_executable_path(binary_name)
                if binary_path is None:
                    raise exceptions.ExecutableNotFoundException(binary_name)

                if binary_path in executable_targets.keys():
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

    def add_edge(self, edge_to_add):
        self._partitionable_graph.add_edge(edge_to_add)

    def create_population(self, size, cellclass, cellparams, structure, label):
        return Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, spinnaker=self,
            multi_cast_vertex=self._multi_cast_vertex)

    def create_projection(self, presynaptic_population,
                          postsynaptic_population, connector, source, target,
                          synapse_dynamics, label, rng):
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

    def _check_if_theres_any_pre_placement_constraints_to_satisify(self):
        for vertex in self._partitionable_graph.vertices:
            virtual_chip_constraints = \
                pacman_utility_calls.locate_constraints_of_type(
                    vertex.constraints,
                    VertexRequiresVirtualChipInMachineConstraint)
            if len(virtual_chip_constraints) > 0:
                for virtual_chip_constraint in virtual_chip_constraints:

                    # check if the virtual chip doesnt already exist
                    if (self._machine.get_chip_at(
                            virtual_chip_constraint.virtual_chip_coords['x'],
                            virtual_chip_constraint.virtual_chip_coords['y'])
                            is None):
                        virutal_chip = \
                            self._create_virtual_chip(virtual_chip_constraint)
                        self._machine.add_chip(virutal_chip)

    def _create_virtual_chip(self, virtual_chip_constraint):
        sdram_object = SDRAM()

        # creates the two links
        to_virtual_chip_link = Link(
            destination_x=virtual_chip_constraint.virtual_chip_coords['x'],
            destination_y=virtual_chip_constraint.virtual_chip_coords['y'],
            source_x=virtual_chip_constraint.connected_to_chip_coords['x'],
            source_y=virtual_chip_constraint.connected_to_chip_coords['y'],
            multicast_default_from=(virtual_chip_constraint
                                    .connected_to_chip_link_id + 3) % 6,
            multicast_default_to=(virtual_chip_constraint
                                  .connected_to_chip_link_id + 3) % 6,
            source_link_id=virtual_chip_constraint.connected_to_chip_link_id)

        from_virtual_chip_link = Link(
            destination_x=(virtual_chip_constraint
                           .connected_to_chip_coords['x']),
            destination_y=(virtual_chip_constraint
                           .connected_to_chip_coords['y']),
            source_x=virtual_chip_constraint.virtual_chip_coords['x'],
            source_y=virtual_chip_constraint.virtual_chip_coords['y'],
            multicast_default_from=(virtual_chip_constraint
                                    .connected_to_chip_link_id + 3) % 6,
            multicast_default_to=(virtual_chip_constraint
                                  .connected_to_chip_link_id + 3) % 6,
            source_link_id=virtual_chip_constraint.connected_to_chip_link_id)

        # create the router
        links = [from_virtual_chip_link]
        router_object = MachineRouter(
            links=links, emergency_routing_enabled=False,
            clock_speed=MachineRouter.ROUTER_DEFAULT_CLOCK_SPEED,
            n_available_multicast_entries=sys.maxint,
            diagnostic_filters=list())

        # create the processors
        processors = list()
        for virtual_core_id in range(0, 128):
            processors.append(Processor(virtual_core_id,
                                        Processor.CPU_AVAILABLE,
                                        virtual_core_id == 0))

        # connect the real chip with the virtual one
        connected_chip = self._machine.get_chip_at(
            virtual_chip_constraint.connected_to_chip_coords['x'],
            virtual_chip_constraint.connected_to_chip_coords['y'])
        connected_chip.router.add_link(to_virtual_chip_link)

        # return new v chip
        return Chip(
            processors=processors, router=router_object, sdram=sdram_object,
            x=virtual_chip_constraint.virtual_chip_coords['x'],
            y=virtual_chip_constraint.virtual_chip_coords['y'], virtual=True)

    def stop(self, app_id, stop_on_board=True):
        if stop_on_board:
            for router_table in self._router_tables.routing_tables:
                if len(router_table.multicast_routing_entries) > 0:
                    self._txrx.clear_multicast_routes(router_table.x,
                                                      router_table.y)
                    self._txrx.clear_router_diagnostic_counters(router_table.x,
                                                                router_table.y)
                    # self._txrx.\
                    #    clear_router_diagnostic_non_default_positioned_filters(
                    #        router_table.x, router_table.y)
            # self._txrx.send_signal(app_id, SCPSignal.STOP)
        if self._create_database:
            self._database_thread.stop()

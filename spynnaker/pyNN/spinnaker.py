#pacman imports
from pacman.model.constraints.\
    vertex_requires_virtual_chip_in_machine_constraint import \
    VertexRequiresVirtualChipInMachineConstraint
from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge
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


#spinnmachine imports
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router as MachineRouter
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.chip import Chip


#internal imports
from spinnman.messages.scp.scp_signal import SCPSignal
from spinnman.model.iptag.reverse_iptag import ReverseIPTag
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.abstract_models.abstract_iptagable_vertex import \
    AbstractIPTagableVertex
from spynnaker.pyNN.models.abstract_models.abstract_reverse_iptagable_vertex import \
    AbstractReverseIPTagableVertex
from spynnaker.pyNN.models.utility_models.command_sender import CommandSender
from spynnaker.pyNN.spynnaker_comms_functions import SpynnakerCommsFunctions
from spynnaker.pyNN.spynnaker_configuration import SpynnakerConfiguration
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import reports
from spynnaker.pyNN.models.utility_models.live_packet_gather\
    import LivePacketGather
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN.overridden_pacman_functions.graph_edge_filter \
    import GraphEdgeFilter

#spinnman inports
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset

import logging
import math
import sys
import time

logger = logging.getLogger(__name__)


class Spinnaker(SpynnakerConfiguration, SpynnakerCommsFunctions):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None):
        SpynnakerConfiguration.__init__(self, host_name, graph_label)

        if self._app_id is None:
            self._set_up_main_objects()
            self._set_up_pacman_algorthms_listings()
            self._set_up_executable_specifics()
            self._set_up_report_specifics()
            self._set_up_output_application_data_specifics()
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)

        SpynnakerCommsFunctions.__init__(self, self._reports_states,
                                         self._report_default_directory)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)
    
        #get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))
        self._edge_count = 0

    def run(self, run_time):
        self._setup_interfaces(hostname=self._hostname)

        #set up vis if needed
        if conf.config.getboolean("Visualiser", "enable"):
            self._visualiser, self._visualiser_vertex_to_page_mapping =\
                self._setup_visuliser(
                    self._partitionable_graph, self._visualiser_vertices,
                    self._partitioned_graph, self._placements,
                    self._router_tables, self._runtime, self._machine_time_step,
                    self._graph_mapper)

        #create network report if needed
        if self._reports_states is not None:
            reports.network_specification_report(self._report_default_directory,
                                                 self._partitionable_graph,
                                                 self._hostname)

        #calcualte number of machien time steps
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
                vertex.set_no_machine_time_steps(self._no_machine_time_steps)
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

        #extract iptags required by the graph
        self._set_iptags()
        self._set_reverse_ip_tags()

        #execute data spec generation
        if do_timing:
            timer.start_timing()
        logger.info("*** Generating Output *** ")
        logger.debug("")
        executable_targets = self.generate_data_specifications()
        if do_timing:
            timer.take_sample()

        #execute data spec execution
        if do_timing:
            timer.start_timing()
        processor_to_app_data_base_address = \
            self.execute_data_specification_execution(
                conf.config.getboolean("SpecExecution", "specExecOnHost"),
                self._hostname, self._placements, self._graph_mapper)

        #engage vis if requested
        if do_timing:
            timer.take_sample()

        if conf.config.getboolean("Visualiser", "enable"):
            self.start_visualiser()

        if conf.config.getboolean("Execute", "run_simulation"):
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
                    self._app_id)
                logger.info("*** Loading executables ***")
                self._load_executable_images(executable_targets, self._app_id)
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

                self._start_execution_on_machine(executable_targets,
                                                 self._app_id, self._runtime)
                self._has_ran = True
                if self._retrieve_provance_data:
                    #retrieve provance data
                    self._retieve_provance_data_from_machine(executable_targets)
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
        #extract reverse iptags required by the graph
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
                    vertex.set_reverse_iptag_tag(self._current_max_tag_value + 1)
                    self._current_max_tag_value += 1
                    reverse_iptag = self._create_reverse_iptag_from_iptag(
                        reverse_iptag, vertex)
                    self._add_reverse_tag(reverse_iptag)

    def _create_reverse_iptag_from_iptag(self, reverse_iptag, vertex):
        subverts = self._graph_mapper.get_subvertices_from_vertex(vertex)
        if len(subverts) > 1:
            raise exceptions.ConfigurationException(
                "reverse iptaggable populations can only be supported if they"
                " are partitoned in a 1 to 1 ratio. Please reduce the number "
                "of neurons per core, or the max-atoms per core to support a "
                "one core mapping for your iptaggable population.")
        subvert = next(iter(subverts))
        placement = self._placements.get_placement_of_subvertex(subvert)
        return ReverseIPTag(
            address=reverse_iptag.address, port=reverse_iptag.port,
            tag=reverse_iptag.tag, destination_x=placement.x,
            destination_y=placement.y, destination_p=placement.p)

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

    def __repr__(self):
        return "Spinnaker object for machine {}".format(self._hostname)

    def map_model(self):
        """
        executes the pacman compilation stack
        """
        pacman_report_state = \
            self._reports_states.generate_pacman_report_states()

        self._check_if_theres_any_pre_placement_constraints_to_satisify()
        
        #execute partitioner
        self._execute_partitioner(pacman_report_state)

        #execute placer
        self._execute_placer(pacman_report_state)

        #execute pynn subedge pruning
        self._partitioned_graph, self._graph_mapper = \
            GraphEdgeFilter().run(self._partitioned_graph, self._graph_mapper)

        #execute key allocator
        self._execute_key_allocator(pacman_report_state)

        #execute router
        self._execute_router(pacman_report_state)

    def _execute_key_allocator(self, pacman_report_state):
        if self._key_allocator_algorithm is None:
            self._key_allocator_algorithm = BasicRoutingInfoAllocator()
        else:
            self._key_allocator_algorithm = self._key_allocator_algorithm()

        #execute routing info generator
        self._routing_infos = \
            self._key_allocator_algorithm.allocate_routing_info(
                self._partitioned_graph, self._placements)

        #generate reports
        if (pacman_report_state is not None and
                pacman_report_state.routing_info_report):
            pacman_reports.routing_info_reports(
                self._report_default_directory, self._hostname,
                self._partitioned_graph, self._placements, self._routing_infos)

    def _execute_router(self, pacman_report_state):
        #set up a default placer algorithm if none are specified
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

    def _execute_partitioner(self, pacman_report_state):
        #execute partitioner or default partitioner (as seen fit)
        if self._partitioner_algorithm is None:
            self._partitioner_algorithm = \
                BasicPartitioner(self._machine_time_step,
                                 self._no_machine_time_steps)
        else:
            self._partitioner_algorithm = \
                self._partitioner_algorithm(self._machine_time_step,
                                            self._no_machine_time_steps)

        # if algorithum needs a placer, add placer algorithum
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
        #execute placer or default placer (as seen fit)
        if self._placer_algorithm is None:
            self._placer_algorithm = BasicPlacer(self._machine)
        else:
            self._placer_algorithm = self._placer_algorithm(self._machine)
        self._placements = self._placer_algorithm.place(self._partitioned_graph)

        #execute placer reports if needed
        if (pacman_report_state is not None and
                pacman_report_state.placer_report):
            pacman_reports.placer_reports(
                graph=self._partitionable_graph,
                graph_mapper=self._graph_mapper, hostname=self._hostname,
                machine=self._machine, placements=self._placements,
                report_folder=self._report_default_directory)

    def generate_data_specifications(self):
        #iterate though subvertexes and call generate_data_spec for each vertex
        executable_targets = dict()

        #create a progress bar for end users
        progress_bar = ProgressBar(len(list(self._placements.placements)),
                                   "on generating data specifications")

        for placement in self._placements.placements:
            associated_vertex =\
                self._graph_mapper.get_vertex_from_subvertex(
                    placement.subvertex)
            # if the vertex can generate a DSG, call it
            if isinstance(associated_vertex, AbstractDataSpecableVertex):
                associated_vertex.generate_data_spec(
                    placement.subvertex, placement, self._partitioned_graph,
                    self._partitionable_graph, self._routing_infos,
                    self._hostname, self._graph_mapper,
                    self._report_default_directory)

                binary_name = associated_vertex.get_binary_file_name()
                if binary_name in executable_targets.keys():
                    executable_targets[binary_name].add_processor(placement.x,
                                                                  placement.y,
                                                                  placement.p)
                else:
                    processors = [placement.p]
                    initial_core_subset = CoreSubset(placement.x, placement.y,
                                                     processors)
                    list_of_core_subsets = [initial_core_subset]
                    executable_targets[binary_name] = \
                        CoreSubsets(list_of_core_subsets)
            #update the progress bar
            progress_bar.update()
        #finish the progress bar
        progress_bar.end()
        return executable_targets

    def start_visualiser(self):
        """starts the port listener and ties it to the visualiser_framework pages as
         required
        """
       #register a listener at the trasnciever for each visualised vertex
        for vertex in self._visualiser_vertices:
            if vertex in self._visualiser_vertex_to_page_mapping.keys():
                associated_page = self._visualiser_vertex_to_page_mapping[vertex]
                self._txrx.register_listener(associated_page.recieved_spike(),
                                             self._hostname)
        self._visualiser.start()

    def add_vertex(self, vertex_to_add):
        if isinstance(vertex_to_add, CommandSender):
            self._multi_cast_vertex = vertex_to_add
        self._partitionable_graph.add_vertex(vertex_to_add)

    def add_edge(self, edge_to_add):
        self._partitionable_graph.add_edge(edge_to_add)

    def create_visualised_population(self, size, cellclass, cellparams,
                                     structure, label):
        requires_visualiser = conf.config.getboolean("Visualiser", "enable")
        if not requires_visualiser:
            raise exceptions.ConfigurationException(
                "The visualiser is currently turned off by a spinnaker.cfg or "
                "pacman.cfg file. Please correct and try again.")
        else:
            from spynnaker.pyNN.visualiser_package.visualised_vertex \
                import VisualisedVertex
            return VisualisedVertex(
                size=size, cellclass=cellclass, cellparams=cellparams,
                structure=structure, label=label, spinnaker=self,
                multi_cast_vertex=self._multi_cast_vertex)

    def create_population(self, size, cellclass, cellparams, structure, label):
        return Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, spinnaker=self,
            multi_cast_vertex=self._multi_cast_vertex)

    def create_projection(self, presynaptic_population, postsynaptic_population,
                          connector, source, target, synapse_dynamics, label,
                          rng):
        if label is None:
            label = "Projection {}".format(self._edge_count)
            self._edge_count += 1
        return Projection(
            presynaptic_population=presynaptic_population, label=label,
            postsynaptic_population=postsynaptic_population, rng=rng,
            connector=connector, source=source, target=target,
            synapse_dynamics=synapse_dynamics, spinnaker_control=self,
            machine_time_step=self._machine_time_step)

    def add_edge_to_recorder_vertex(self, vertex_to_record_from):
        #check to see if it needs to be created in the frist place
        if self._live_spike_recorder is None:
            port = None
            if conf.config.has_option("Recording", "live_spike_port"):
                port = conf.config.getint("Recording", "live_spike_port")
            hostname = "localhost"
            if conf.config.has_option("Recording", "live_spike_host"):
                hostname = conf.config.get("Recording", "live_spike_host")
            tag = None
            if conf.config.has_option("Recording", "live_spike_tag"):
                tag = conf.config.getint("Recording", "live_spike_tag")
            if tag is None:
                raise exceptions.ConfigurationException(
                    "Target tag for live spikes has not been set")
            self._live_spike_recorder = \
                LivePacketGather(self.machine_time_step, tag, port, hostname)
            self.add_vertex(self._live_spike_recorder)
        #create the edge and add
        edge = PartitionableEdge(vertex_to_record_from,
                                 self._live_spike_recorder, "recorder_edge")
        self.add_edge(edge)

    def add_visualiser_vertex(self, visualiser_vertex_to_add):
        if self._visualiser_vertices is None:
            self._visualiser_vertices = list()
        self._visualiser_vertices.append(visualiser_vertex_to_add)

    def _check_if_theres_any_pre_placement_constraints_to_satisify(self):
        for vertex in self._partitionable_graph.vertices:
            virtual_chip_constraints = \
                pacman_utility_calls.locate_constraints_of_type(
                    vertex.constraints,
                    VertexRequiresVirtualChipInMachineConstraint)
            if len(virtual_chip_constraints) > 0:
                for virtual_chip_constraint in virtual_chip_constraints:
                    #check if the virtual chip doesnt already exist
                    if (self._machine.get_chip_at(
                            virtual_chip_constraint.virtual_chip_coords['x'],
                            virtual_chip_constraint.virtual_chip_coords['y'])
                            is None):
                        virutal_chip = \
                            self._create_virtual_chip(virtual_chip_constraint)
                        self._machine.add_chip(virutal_chip)

    def _create_virtual_chip(self, virtual_chip_constraint):
        sdram_object = SDRAM()
        #creates the two links
        to_virtual_chip_link = Link(
            destination_x=virtual_chip_constraint.virtual_chip_coords['x'],
            destination_y=virtual_chip_constraint.virtual_chip_coords['y'],
            source_x=virtual_chip_constraint.connected_to_chip_coords['x'],
            source_y=virtual_chip_constraint.connected_to_chip_coords['y'],
            multicast_default_from=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            multicast_default_to=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            source_link_id=virtual_chip_constraint.connected_to_chip_link_id)

        from_virtual_chip_link = Link(
            destination_x=virtual_chip_constraint.connected_to_chip_coords['x'],
            destination_y=virtual_chip_constraint.connected_to_chip_coords['y'],
            source_x=virtual_chip_constraint.virtual_chip_coords['x'],
            source_y=virtual_chip_constraint.virtual_chip_coords['y'],
            multicast_default_from=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            multicast_default_to=
            (virtual_chip_constraint.connected_to_chip_link_id + 3) % 6,
            source_link_id=virtual_chip_constraint.connected_to_chip_link_id)

        #create the router
        links = [from_virtual_chip_link]
        router_object = MachineRouter(
            links=links, emergency_routing_enabled=False,
            clock_speed=MachineRouter.ROUTER_DEFAULT_CLOCK_SPEED,
            n_available_multicast_entries=sys.maxint)

        #create the processors
        processors = list()
        for virtual_core_id in range(0, 128):
            processors.append(Processor(virtual_core_id,
                                        Processor.CPU_AVAILABLE,
                                        virtual_core_id == 0))
        #connect the real chip with the virtual one
        connected_chip = self._machine.get_chip_at(
            virtual_chip_constraint.connected_to_chip_coords['x'],
            virtual_chip_constraint.connected_to_chip_coords['y'])
        connected_chip.router.add_link(to_virtual_chip_link)
        #return new v chip
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
            time.sleep(0.5)
            self._txrx.send_signal(app_id, SCPSignal.STOP)
        if conf.config.getboolean("Visualiser", "enable"):
            self._visualiser.stop()
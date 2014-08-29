#pacman imports
from pacman.model.constraints.\
    vertex_requires_virtual_chip_in_machine_constraint import \
    VertexRequiresVirtualChipInMachineConstraint
from pacman.model.partitionable_graph.partitionable_edge \
    import PartitionableEdge
from pacman.operations.partitioner import Partitioner
from pacman.operations.placer import Placer
from pacman.operations.routing_info_allocator import RoutingInfoAllocator
from pacman.operations.router import Router
from pacman.utilities.progress_bar import ProgressBar
from pacman.utilities import utility_calls as pacman_utility_calls


#spinnmachine imports
from spinn_machine.sdram import SDRAM
from spinn_machine.router import Router as MachineRouter
from spinn_machine.link import Link
from spinn_machine.processor import Processor
from spinn_machine.chip import Chip


#internal imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.models.utility_models.multicastsource import MultiCastSource
from spynnaker.pyNN.spynnaker_comms_functions import SpynnakerCommsFunctions
from spynnaker.pyNN.spynnaker_configuration import SpynnakerConfiguration
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.models.utility_models.live_spike_recorder\
    import LiveSpikeRecorder
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN.overridden_pacman_functions.subgraph_subedge_pruning \
    import SubgraphSubedgePruning
from spynnaker.pyNN import reports

#spinnman inports
from spinnman.model.core_subsets import CoreSubsets
from spinnman.model.core_subset import CoreSubset

import logging
import math
import sys

logger = logging.getLogger(__name__)


class Spinnaker(SpynnakerConfiguration, SpynnakerCommsFunctions):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None):
        SpynnakerConfiguration.__init__(self, host_name, graph_label)

        if self._app_id is None:
            self._set_up_main_objects()
            self._set_up_pacman_algorthms_listings()
            self._set_up_executable_specifics()
            self._set_up_recording_specifics()
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
        self._setup_interfaces(
            hostname=self._hostname, machine=self._machine,
            machine_time_step=self.machine_time_step, runtime=self._runtime,
            partitioned_graph=self._partitioned_graph,
            placements=self._placements, router_tables=self._router_tables,
            partitionable_graph=self._partitionable_graph,
            visualiser_vertices=self._visualiser_vertices)

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

            if self._do_load is True:
                logger.info("*** Loading data ***")
                self._load_application_data(self._placements,
                                            self._graph_mapper,
                                            processor_to_app_data_base_address,
                                            self._hostname)
                logger.info("*** Loading executables ***")
                self._load_executable_images(executable_targets, self._app_id)
            if do_timing:
                timer.take_sample()

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                self._start_execution_on_machine(executable_targets,
                                                 self._app_id, self._runtime)
                self._has_ran = True
                if self._retrieve_provance_data:
                    #retrieve provance data
                    self._retieve_provance_data_from_machine(executable_targets)
        else:
            logger.info("*** No simulation requested: Stopping. ***")

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
    def sub_graph(self):
        return self._partitioned_graph

    @property
    def partitionable_graph(self):
        return self._partitionable_graph

    @property
    def graph_mapper(self):
        return self._graph_mapper

    def set_app_id(self, value):
        self._app_id = value

    def set_runtime(self, value):
        self._runtime = value

    def map_model(self):
        """
        executes the pacman compilation stack
        """
        pacman_report_state = \
            self._reports_states.generate_pacman_report_states()

        self._check_if_theres_any_pre_placement_constraints_to_satisify()
        
        #execute partitioner
        partitioner = Partitioner(
            partition_algorithm=self._partitioner_algorithm,
            machine_time_step=self._machine_time_step,
            no_machine_time_steps=self._no_machine_time_steps,
            report_folder=self._report_default_directory,
            report_states=pacman_report_state, hostname=self._hostname,
            placer_algorithm=self._placer_algorithm, machine=self._machine)
        self._partitioned_graph, self._graph_mapper = \
            partitioner.run(self._partitionable_graph)

        #execute placer
        placer = Placer(
            machine=self._machine, report_states=pacman_report_state,
            report_folder=self._report_default_directory,
            partitonable_graph=self._partitionable_graph,
            hostname=self._hostname, placer_algorithm=self._placer_algorithm)
        self._placements = \
            placer.run(self._partitioned_graph, self._graph_mapper)

        #execute pynn subedge pruning
        pruner = SubgraphSubedgePruning()
        self._partitioned_graph, self._graph_mapper = \
            pruner.run(self._partitioned_graph, self._graph_mapper)

        #execute key allocator
        key_allocator = RoutingInfoAllocator(
            report_states=pacman_report_state, hostname=self._hostname,
            report_folder=self._report_default_directory, machine=self._machine,
            graph_mapper=self._graph_mapper,
            routing_info_allocator_algorithm=self._key_allocator_algorithm)
        self._routing_infos = key_allocator.run(self._partitioned_graph,
                                                self._placements)

        #execute router
        router = Router(report_folder=self._report_default_directory,
                        report_states=self._reports_states,
                        partitionable_graph=self._partitionable_graph,
                        graph_mappings=self._graph_mapper)
        self._router_tables = router.run(
            self._routing_infos, self._placements, self._machine,
            self._partitioned_graph)

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
                    self._hostname, self._graph_mapper)

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
        """starts the port listener and ties it to the visualiser pages as
         required
        """
       #register a listener at the trasnciever for each visualised vertex
        for vertex in self._visualiser_vertices:
            associated_page = self._visualiser_vertex_to_page_mapping[vertex]
            if associated_page is not None:
                self._txrx.register_listener(associated_page.recieved_spike(),
                                             self._hostname)
        self._visualiser.start()

    def add_vertex(self, vertex_to_add):
        if type(vertex_to_add) == \
                type(MultiCastSource(self._machine_time_step)):
            self._multi_cast_vertex = vertex_to_add
        self._partitionable_graph.add_vertex(vertex_to_add)

    def add_edge(self, edge_to_add):
        self._partitionable_graph.add_edge(edge_to_add)

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
            self._live_spike_recorder = \
                LiveSpikeRecorder(self.machine_time_step)
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
                for virutal_chip_constrant in virtual_chip_constraints:
                    #check if the virtual chip doesnt already exist
                    if (self._machine.get_chip_at(
                            virutal_chip_constrant.virtual_chip_coords['x'],
                            virutal_chip_constrant.virtual_chip_coords['y'])
                            is None):
                        virutal_chip = \
                            self._create_virtual_chip(virutal_chip_constrant)
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
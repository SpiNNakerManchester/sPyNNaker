#pacman imports
from pacman.model.graph.graph import Graph
from pacman.model.graph.edge import Edge
from pacman.operations import partition_algorithms
from pacman.operations import placer_algorithms
from pacman.operations import router_algorithms
from pacman.operations import routing_info_allocator_algorithms
from pacman.operations.partitioner import Partitioner
from pacman.operations.placer import Placer
from pacman.operations.router import Router
from pacman.operations.routing_info_allocator import RoutingInfoAllocator
from pacman import reports as pacman_reports

#internal imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.report_states import ReportState
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.utility_models.live_spike_recorder\
    import LiveSpikeRecorder
from spynnaker.pyNN.visualiser_package.visualiser_creation_utility \
    import VisualiserCreationUtility
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.models.pynn_projection import Projection
from spynnaker.pyNN import overrided_pacman_functions

#spinnman inports
from spinnman.transceiver import create_transceiver_from_hostname
from spinnman.model.iptag import IPTag

#data spec import
from data_specification.file_data_reader import FileDataReader
from data_specification.file_data_writer import FileDataWriter
from data_specification.data_specification_executor\
    import DataSpecificationExecutor

import logging
import math

logger = logging.getLogger(__name__)


class Spinnaker(object):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None):
        self._hostname = host_name
        self._time_scale_factor = None
        #specific utility vertexes
        self._live_spike_recorder = None
        self._multi_cast_vertex = None
        self._txrx = None
        #visualiser objects
        self._visualiser = None
        self._wait_for_run = False
        self._visualiser_port = None
        self._visualiser_vertices = None
        self._visualiser_creation_utility = VisualiserCreationUtility()

        #main objects
        self._graph = Graph(label=graph_label)
        self._sub_graph = None
        self._graph_subgraph_mapper = None
        self._machine = None
        self._no_machine_time_steps = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._pruner_infos = None
        self._runtime = None
        self._has_ran = False
        self._reports_enabled = None

        #report object
        if conf.config.getboolean("Reports", "reportsEnabled"):
            self._reports_enabled = ReportState()

        #communication objects
        self._iptags = list()

        self._app_id = conf.config.getint("Machine", "appID")
        self._machine_time_step = conf.config.getint("Machine",
                                                     "machineTimeStep")
        self._writeTextSpecs = False
        if conf.config.getboolean("Reports", "reportsEnabled"):
            self._writeTextSpecs = conf.config.getboolean("Reports",
                                                          "writeTextSpecs")
        #algorithum lists
        partitioner_algorithms_list = \
            conf.get_valid_components(partition_algorithms, "Partitioner")
        self._partitioner_algorithum = \
            partitioner_algorithms_list[conf.config.get("Partitioner",
                                                        "algorithm")]

        placer_algorithms_list = \
            conf.get_valid_components(placer_algorithms, "Placer")
        self._placer_algorithum = \
            placer_algorithms_list[conf.config.get("Placer", "algorithm")]

        #get common key allocator algorithms
        key_allocator_algorithms_list = \
            conf.get_valid_components(routing_info_allocator_algorithms,
                                      "RoutingInfoAllocator")
        #get pynn specific key allocator
        pynn_overloaded_allocator = \
            conf.get_valid_components(overrided_pacman_functions,
                                      "RoutingInfoAllocator")
        key_allocator_algorithms_list.update(pynn_overloaded_allocator)

        self._key_allocator_algorithum = \
            key_allocator_algorithms_list[conf.config.get("KeyAllocator",
                                                          "algorithm")]

        routing_algorithms_list = \
            conf.get_valid_components(router_algorithms, "Routing")
        self._routing_algorithm = \
            routing_algorithms_list[conf.config.get("Routing", "algorithm")]

        #loading and running config params
        self._do_load = True
        if conf.config.has_option("Execute", "load"):
            self._do_load = conf.config.getboolean("Execute", "load")

        self._do_run = True
        if conf.config.has_option("Execute", "run"):
            self._do_run = conf.config.getboolean("Execute", "run")

        #central stuff
        if host_name is not None:
            self._hostname = host_name
            logger.warn("The machine name from PYNN setup is overriding the "
                        "machine name defined in the pacman.cfg file")
        elif conf.config.has_option("Machine", "machineName"):
            self._hostname = conf.config.get("Machine", "machineName")
        else:
            raise Exception("A SpiNNaker machine must be specified in "
                            "pacman.cfg.")
        if self._hostname == 'None':
            raise Exception("A SpiNNaker machine must be specified in "
                            "pacman.cfg.")

        #deal with params allowed via the setup optimals
        if timestep is not None:
            timestep *= 1000  # convert into ms from microseconds
            conf.config.set("Machine", "machineTimeStep", timestep)
        if min_delay is not None and float(min_delay * 1000) < 1.0 * timestep:
            raise exceptions.ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step".format(1.0 * timestep))
    
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
            raise exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(0.144 * timestep))
        if min_delay is not None:
            if not conf.config.has_section("Model"):
                conf.config.add_section("Model")
            conf.config.set("Model", "min_delay", (min_delay * 1000) / timestep)
    
        if max_delay is not None:
            if not conf.config.has_section("Model"):
                conf.config.add_section("Model")
            conf.config.set("Model", "max_delay", (max_delay * 1000) / timestep)
    
        if (conf.config.has_option("Machine", "timeScaleFactor")
                and conf.config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = conf.config.getint("Machine",
                                                         "timeScaleFactor")
            if timestep * self._time_scale_factor < 1000:
                logger.warn("the combination of machine time step and the "
                            "machine time scale factor results in a real timer "
                            "tic that is currently not reliably supported by "
                            "the spinnaker machine.")
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
                
        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)
    
        #get the machien time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

        if conf.config.has_option("Recording", "send_live_spikes"):
            if conf.config.getboolean("Recording", "send_live_spikes"):
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

                # Set up the forwarding so that monitored spikes are sent to the
                # requested location
                self._set_tag_output(tag, port, hostname)
                #takes the same port for the visualiser if being used
                if conf.config.getboolean("Visualiser", "enable") and \
                   conf.config.getboolean("Visualiser", "have_board"):
                    self._visualiser_creation_utility.set_visulaiser_port(port)

        self._edge_count = 0

    def run(self, run_time):
        self._setup_interfaces()
        #calcualte number of machien time steps
        if run_time is not None:
            self._no_machine_time_steps =\
                int((run_time * 1000.0) / self.machine_time_step)
            ceiled_machine_time_steps = \
                math.ceil((run_time * 1000.0) / self.machine_time_step)
            if self._no_machine_time_steps != ceiled_machine_time_steps:
                raise exceptions.ConfigurationException(
                    "The runtime and machine time step combination result in "
                    "a factional number of machine runable time steps and "
                    "therefore spinnaker cannot determine how many to run for")
        else:
            self._no_machine_time_steps = None
            logger.warn("You have set a runtime that will never end, this may"
                        "cause the neural models to fail to partition "
                        "correctly")

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

        if do_timing:
            timer.start_timing()
        logger.info("*** Generating Output *** ")
        logger.debug("")
        executable_targets = self.generate_data_specifications()
        if do_timing:
            timer.take_sample()

        if do_timing:
            timer.start_timing()
        self.execute_data_specification_execution(
            conf.config.getboolean("SpecExecution", "specExecOnHost"),
            self._hostname)
        if do_timing:
            timer.take_sample()

        self.start_visualiser()

        if do_timing:
            timer.start_timing()
        if conf.config.getboolean("Execute", "run_simulation"):
            if self._do_load is True:
                logger.info("*** Loading data ***")
                #TODO need to convert this into spinnman calls and use spinnman objects
                _controller.load_targets()
                _controller.load_write_mem()
            if do_timing:
                timer.take_sample()

            if self._do_run is True:
                logger.info("*** Running simulation... *** ")
                self._run(executable_targets)
        else:
            logger.info("*** No simulation requested: Stopping. ***")

    def _setup_interfaces(self):
        """Set up the interfaces for communicating with the SpiNNaker board
        """
        has_board = conf.config.getboolean("Machine", "have_board")

        if has_board:
            self._txrx = create_transceiver_from_hostname(self._hostname)
        self._machine = self._txrx.get_machine_details()

        self._visualiser = \
            self._visualiser_creation_utility.create_visualiser_interface(
                has_board, self._txrx, self._graph, self._visualiser_vertices,
                self._machine, self._sub_graph, self._placements,
                self._router_tables, self._runtime, self._machine_time_step)

    @property
    def app_id(self):
        return self._app_id

    @property
    def machine_time_step(self):
        return self._machine_time_step

    @property
    def sub_graph(self):
        return self._sub_graph

    @property
    def graph(self):
        return self._graph

    def set_app_id(self, value):
        self._app_id = value

    def set_runtime(self, value):
        self._runtime = value

    def map_model(self):
        """
        executes the pacman compilation stack
        """

        #execute partitioner
        partitoner = Partitioner(self._partitioner_algorithum)
        self._sub_graph, self._graph_subgraph_mapper = \
            partitoner.run(self._graph, self._machine)
        if (self._reports_enabled is not None and
                self._reports_enabled.partitioner_report):
            pacman_reports.partitioner_report()

        #execute placer
        placer = Placer(self._placer_algorithum)
        self._placements = placer.run(self._sub_graph, self._machine)
        if (self._reports_enabled is not None and
                self._reports_enabled.placer_report):
            pacman_reports.placer_report()

        #execute key allocator
        key_allocator = RoutingInfoAllocator(self._key_allocator_algorithum)
        self._routing_infos = key_allocator.run(self._graph_subgraph_mapper,
                                                self._placements)
        if (self._reports_enabled is not None and
                self._reports_enabled.routing_info_report):
            pacman_reports.routing_info_report()

        #execute router
        router = Router(self._routing_algorithm)
        self._router_tables = router.run(self._routing_infos, self._placements,
                                         self._machine)
        if (self._reports_enabled is not None and
                self._reports_enabled.router_report):
            pacman_reports.router_report()

    def generate_data_specifications(self):
        #iterate though subvertexes and call generate_data_spec for each vertex
        executable_targets = dict()

        for placement in self._placements():
            associated_vertex =\
                self._sub_graph.get_vertex_from_subvertex(placement.subvertex)
            # if the vertex can generate a DSG, call it
            if issubclass(associated_vertex, AbstractDataSpecableVertex):
                associated_vertex.generate_data_spec(
                    placement.x, placement.y, placement.p, placement.subvertex,
                    self._sub_graph, self._routing_infos)

                binary_name = associated_vertex.get_binary_name()
                if binary_name in executable_targets.keys():
                    executable_targets[binary_name].append({'x': placement.x,
                                                            'y': placement.y,
                                                            'p': placement.p})
                else:
                    executable_targets[binary_name] = list({'x': placement.x,
                                                            'y': placement.y,
                                                            'p': placement.p})
        return executable_targets

    def execute_data_specification_execution(self, host_based_execution,
                                             hostname):
        if host_based_execution:
            self._execute_host_based_data_specificiation_execution(hostname)
        else:
            self._chip_based_data_specificiation_execution(hostname)

    def _chip_based_data_specificiation_execution(self, hostname):
        raise NotImplementedError

    def _execute_host_based_data_specificiation_execution(self, hostname):
        for placement in self._placements():
            associated_vertex =\
                self._sub_graph.get_vertex_from_subvertex(placement.subvertex)
            # if the vertex can generate a DSG, call it
            if issubclass(associated_vertex, AbstractDataSpecableVertex):
                data_spec_file_path = \
                    associated_vertex.get_binary_file_name(
                        placement.x, placement.y, placement.p, hostname
                    )
                app_data_file_path = \
                    associated_vertex.get_application_data_file_name(
                        placement.x, placement.y, placement.p, hostname
                    )
                data_spec_reader = FileDataReader(data_spec_file_path)
                data_writer = FileDataWriter(app_data_file_path)
                host_based_data_spec_exeuctor = DataSpecificationExecutor(
                    data_spec_reader, data_writer)
                bytes_used_by_spec = host_based_data_spec_exeuctor.execute()



    def start_visualiser(self):
        pass

    def stop(self):
        pass

    def _run(self, executable_targets):
        pass

    def _set_tag_output(self, tag, port, hostname):
        self._iptags.append(IPTag(tag=tag, port=port, address=hostname))

    def add_vertex(self, vertex_to_add):
        self._graph.add_vertex(vertex_to_add)

    def add_edge(self, edge_to_add):
        self._graph.add_edge(edge_to_add)

    def create_population(self, size, cellclass, cellparams, structure, label):

        population = Population(
            size=size, cellclass=cellclass, cellparams=cellparams,
            structure=structure, label=label, runtime=self._runtime,
            machine_time_step=self._machine_time_step, spinnaker=self)
        return population

    def create_projection(self, presynaptic_population, postsynaptic_population,
                          connector, source, target, synapse_dynamics, label,
                          rng):
        if label is None:
            label = "Projection {}".format(self._edge_count)
            self._edge_count += 1
        edge = Projection(
            presynaptic_population=presynaptic_population, label=label,
            postsynaptic_population=postsynaptic_population, rng=rng,
            connector=connector, source=source, target=target,
            synapse_dynamics=synapse_dynamics, spinnaker_control=self)

    def add_edge_to_recorder_vertex(self, vertex_to_record_from):
        #check to see if it needs to be created in the frist place
        if self._live_spike_recorder is None:
            self._live_spike_recorder = LiveSpikeRecorder()
            self.add_vertex(self._live_spike_recorder)
        #create the edge and add
        edge = Edge(vertex_to_record_from, self._live_spike_recorder,
                    "recorder_edge")
        self.add_edge(edge)

    def add_visualiser_vertex(self, visualiser_vertex_to_add):
        if self._visualiser_vertices is None:
            self._visualiser_vertices = list()
        self._visualiser_vertices.append(visualiser_vertex_to_add)

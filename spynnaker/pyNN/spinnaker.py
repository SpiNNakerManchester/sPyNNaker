__author__ = 'stokesa6'
#pacman imports
from pacman.model.graph.graph import Graph
from pacman.operations import partition_algorithms
from pacman.operations import placer_algorithms
from pacman.operations import router_algorithms
from pacman.operations import pruner_algorithms
from pacman.operations import routing_info_allocator_algorithms

#machine imports
from spinn_machine.machine import Machine

#internal imports
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.utilities.timer import Timer
from spynnaker.pyNN.models.neural_projections.delay_extension\
    import DelayExtension
from spynnaker.pyNN.models.utility_models.live_spike_recorder\
    import LiveSpikeRecorder
from spynnaker.pyNN.visualiser_package.visualiser_creation_utility \
    import VisualiserCreationUtility
from spynnaker.pyNN.models.abstract_models.population import Population
from spynnaker.pyNN.models.abstract_models.projection import Projection

#spinnman inports
from spinnman.transceiver import Transceiver
from spinnman.transceiver import create_transceiver_from_hostname

import logging
import math

logger = logging.getLogger(__name__)


class Spinnaker(VisualiserCreationUtility, object):

    def __init__(self, host_name=None, timestep=None, min_delay=None,
                 max_delay=None, graph_label=None):
        VisualiserCreationUtility.__init__(self, self)
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

        #main objects
        self._graph = Graph(label=graph_label)
        self.sub_graph = None
        self._machine = None
        self._placements = None
        self._router_tables = None
        self._routing_infos = None
        self._pruner_infos = None
        self._runtime = None

        self._app_id = conf.config.getint("Machine", "appID")
        self._machine_time_step = conf.config.getint("Machine",
                                                     "machineTimeStep")
        self._writeTextSpecs = False
        if conf.config.getboolean("Reports", "reportsEnabled"):
            self._writeTextSpecs = conf.config.getboolean("Reports",
                                                          "writeTextSpecs")
        #algorithum lists
        self._partitioner_algorithms_list = \
            conf.get_valid_components(partition_algorithms, "Partitioner")

        self._placer_algorithms_list = \
            conf.get_valid_components(placer_algorithms, "Placer")

        self._key_allocator_algorithms_list = \
            conf.get_valid_components(routing_info_allocator_algorithms,
                                      "KeyAllocator")

        self._routing_algorithms_list = \
            conf.get_valid_components(router_algorithms, "Routing")

        self._pruner_algorithms_list = \
            conf.get_valid_components(pruner_algorithms, "Pruner")

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
            DelayExtension.MAX_SUPPORTED_DELAY_TICS
        delay_extention_max_supported_delay = \
            DelayExtension.MAX_DELAY_BLOCKS \
            * DelayExtension.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK
    
        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extention_max_supported_delay
    
        if max_delay is not None\
           and float(max_delay * 1000) > max_delay_tics_supported * timestep:
            raise exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(0.144 * timestep))
        if min_delay is not None:
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
                
        logger.info("Setting time scale factor to {%d}."
                    .format(self._time_scale_factor))

        logger.info("Setting appID to %d." % self._app_id)
    
        #get the machien time step
        logger.info("Setting machine time step to {%d} micro-seconds."
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
                self._set_tag_output(tag, port, hostname, 10)
                #takes the same port for the visualiser if being used
                if conf.config.getboolean("Visualiser", "enable") and \
                   conf.config.getboolean("Visualiser", "have_board"):
                    self._set_visulaiser_port(port)

    def run(self, run_time):
        self._setup_spinnman_interfaces()
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
        self.generate_output()
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
                self._run()
        else:
            logger.info("*** No simulation requested: Stopping. ***")

    def _setup_spinnman_interfaces(self):
        """Set up the interfaces for communicating with the SpiNNaker board
        """
        has_board = conf.config.getboolean("Machine", "have_board")

        if has_board:
            self._txrx = create_transceiver_from_hostname(self._hostname)
        self._machine = Machine(self._txrx.get_machine_chip_details())

        self._visualiser = \
            self._create_visualiser_interface(
                has_board, self._txrx, self._graph, self._machine,
                self._placements, self._router_tables, self._runtime,
                self._machine_time_step)

    @property
    def app_id(self):
        return self._app_id

    @property
    def machine_time_step(self):
        return self._machine_time_step

    def set_app_id(self, value):
        self._app_id = value

    def set_runtime(self, value):
        self._runtime = value

    def map_model(self):
        pass

    def generate_output(self):
        pass

    def start_visualiser(self):
        pass

    def stop(self):
        pass

    def _run(self):
        pass

    def _set_tag_output(self, tag, port, hostname, position):
        pass

    def add_vertex(self, vertex_to_add):
        pass

    def add_edge(self, edge_to_add):
        pass

    def create_population(self, size, cellclass, cellparams, structure, label):
        vertex = Population(size, cellclass, cellparams, structure, label)
        self.add_vertex(vertex)

    def create_projection(self, presynaptic_population, postsynaptic_population,
                          connector, source, target, synapse_dynamics, label,
                          rng):
        edge = Projection(presynaptic_population, postsynaptic_population,
                          connector, source, target, synapse_dynamics, label,
                          rng)
        self.add_edge(edge)
        pass

    def add_edge_to_recorder_vertex(self, vertex_to_record_from):
        #check to see if it needs to be created in the frist place
        if self._live_spike_recorder is None:
            self._live_spike_recorder = LiveSpikeRecorder()
            self.add_vertex(self._live_spike_recorder)
        #create the edge and add
            pass

    def add_visualiser_vertex(self, visualiser_vertex_to_add):
        if self._visualiser_vertices is None:
            self._visualiser_vertices = list()
        self._visualiser_vertices.append(visualiser_vertex_to_add)





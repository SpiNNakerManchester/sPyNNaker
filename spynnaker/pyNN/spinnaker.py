
# pacman imports
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge

# common front end imports
from spinn_front_end_common.interface.spinnaker_main_interface import \
    SpinnakerMainInterface
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities.utility_objs.executable_finder \
    import ExecutableFinder

# local front end imports
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
from spynnaker.pyNN import _version

# general imports
import logging
import math
import os

# global objects
logger = logging.getLogger(__name__)
executable_finder = ExecutableFinder()


class Spinnaker(SpinnakerMainInterface):
    """
    Spinnaker: the main entrance for the spynnaker front end
    """

    def __init__(
            self, host_name=None, timestep=None, min_delay=None, max_delay=None,
            graph_label=None, database_socket_addresses=None):

        # Determine default executable folder location
        # and add this default to end of list of search paths
        executable_finder.add_path(os.path.dirname(model_binaries.__file__))

        # create xml path for where to locate spynnaker related functions when
        # using auto pause and resume
        extra_algorithm_xml_path = list()
        extra_algorithm_xml_path.append(os.path.join(
            os.path.dirname(overridden_pacman_functions.__file__),
            "algorithms_metadata.xml"))

        # create list of extra algorithms for auto pause and resume
        extra_algorithms_for_auto_pause_and_resume =\
            ["SpyNNakerRecordingExtractor",
             "SpyNNakerRuntimeUpdaterAfterRun"]

        SpinnakerMainInterface.__init__(
            self, config, _version, host_name=host_name,
            graph_label=graph_label, this_executable_finder=executable_finder,
            database_socket_addresses=database_socket_addresses,
            extra_algorithm_xml_paths=extra_algorithm_xml_path,
            extra_algorithms_for_auto_pause_and_resume=
            extra_algorithms_for_auto_pause_and_resume)

        # timing parameters
        self._min_supported_delay = None
        self._max_supported_delay = None
        self._time_scale_factor = None
        self._spikes_per_second = float(config.getfloat(
            "Simulation", "spikes_per_second"))
        self._ring_buffer_sigma = float(config.getfloat(
            "Simulation", "ring_buffer_sigma"))

        # population holders
        self._populations = list()
        self._projections = list()
        self._multi_cast_vertex = None
        self._edge_count = 0
        self._live_spike_recorder = dict()

        # set up machine targeted data
        self._set_up_machine_specifics(timestep, min_delay, max_delay,
                                       host_name)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

    def _create_pacman_executor_inputs(self, this_run_time, is_resetting=False):
        inputs, application_graph_changed, using_auto_pause_and_resume = \
            SpinnakerMainInterface._create_pacman_executor_inputs(
                self, this_run_time, is_resetting)
        if application_graph_changed and not is_resetting:
            inputs.append({
                'type': "ExecuteMapping",
                'value': config.getboolean(
                    "Database", "create_routing_info_to_neuron_id_mapping")})
        return inputs, application_graph_changed, using_auto_pause_and_resume

    def _create_algorithm_list(
            self, debug, application_graph_changed, executing_reset,
            using_auto_pause_and_resume):
        """
        creates the list of algorithms to use within the system
        :param debug: if the tools should be operating in debug mode
        :param application_graph_changed: has the graph changed since last run
        :param executing_reset: are we executing a reset function
        :param using_auto_pause_and_resume: check if the system is to use
        auto pause and resume functionality
        :return: list of algorithms to use and a list of optional
        algorithms to use
        """
        # generate algorithm list from front end config
        mapping_algorithms = list()

        virtual_board = config.getboolean("Machine", "virtual_board")

        if not virtual_board:
            # needed for multi-run/SSA's to work correctly.
            mapping_algorithms.append("SpyNNakerRuntimeUpdater")
            # if not in auto pause and resume mode, use front end common
            # chip runtime updater
            if (application_graph_changed and not executing_reset and
                    not using_auto_pause_and_resume):
                mapping_algorithms.append("FrontEndCommonChipRuntimeUpdater")
            if not application_graph_changed and not executing_reset:
                mapping_algorithms.append("FrontEndCommonChipRuntimeUpdater")
            if self._has_ran and not executing_reset:
                mapping_algorithms.append("SpyNNakerRecordingExtractor")

        # get config mapping algorithms and convert as needed
        algorithm_names = config.get("Mapping", "algorithms")
        algorithm_strings = algorithm_names.split(",")
        for algorithm_string in algorithm_strings:
            split_string = algorithm_string.split(":")
            if len(split_string) == 1:
                mapping_algorithms.append(split_string[0])
            else:
                raise common_exceptions.ConfigurationException(
                    "The tool chain expects config params of list of 1 "
                    "element with ,. Where the elements are either: the "
                    "algorithm_name:algorithm_config_file_path, or "
                    "algorithm_name if its a internal to pacman algorithm."
                    " Please rectify this and try again")

        # get common algorithm flow support
        algorithms, optional_algorithms = \
            self._create_all_flows_algorithm_common(
                debug, application_graph_changed, executing_reset,
                using_auto_pause_and_resume)
        mapping_algorithms.extend(algorithms)
        return mapping_algorithms, optional_algorithms

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
                if config.getboolean(
                        "Mode", "violate_1ms_wall_clock_restriction"):
                    logger.warn(
                        "*****************************************************")
                    logger.warn(
                        "*** The combination of simulation time step and   ***")
                    logger.warn(
                        "*** the machine time scale factor results in a    ***")
                    logger.warn(
                        "*** wall clock timer tick that is currently not   ***")
                    logger.warn(
                        "*** reliably supported by the spinnaker machine.  ***")
                    logger.warn(
                        "*****************************************************")
                else:
                    raise common_exceptions.ConfigurationException(
                        "The combination of simulation time step and the"
                        " machine time scale factor results in a wall clock "
                        "timer tick that is currently not reliably supported "
                        "by the spinnaker machine.")
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

    def __repr__(self):
        return "spynnaker front end instance for machine {}"\
            .format(self._hostname)

    def add_partitionable_vertex(self, vertex_to_add):
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
                self.add_partitionable_vertex(self._multi_cast_vertex)
            edge = MultiCastPartitionableEdge(
                self._multi_cast_vertex, vertex_to_add)
            self._multi_cast_vertex.add_commands(vertex_to_add.commands, edge)
            self.add_partitionable_edge(edge)

        # add any dependent edges and vertices if needed
        if isinstance(vertex_to_add,
                      AbstractVertexWithEdgeToDependentVertices):
            for dependant_vertex in vertex_to_add.dependent_vertices:
                self.add_partitionable_vertex(dependant_vertex)
                dependant_edge = MultiCastPartitionableEdge(
                    pre_vertex=vertex_to_add, post_vertex=dependant_vertex)
                self.add_partitionable_edge(
                    dependant_edge,
                    vertex_to_add.edge_partition_identifier_for_dependent_edge)

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

        SpinnakerMainInterface.stop(
            self, turn_off_machine, clear_routing_tables, clear_tags)

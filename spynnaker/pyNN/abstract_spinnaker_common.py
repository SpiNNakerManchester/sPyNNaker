# utils imports
import spinn_utilities.conf_loader as conf_loader
from spinn_utilities.abstract_base import AbstractBase

# common front end imports
from spinn_front_end_common.interface.abstract_spinnaker_base \
    import AbstractSpinnakerBase
from spinn_front_end_common.utilities import exceptions as common_exceptions
from spinn_front_end_common.utilities import helpful_functions
from spinn_front_end_common.utility_models.command_sender import CommandSender
from spinn_front_end_common.utilities.utility_objs.executable_finder \
    import ExecutableFinder
from spinn_front_end_common.utilities import globals_variables

# local front end imports
import spynnaker.pyNN
from spynnaker.pyNN import overridden_pacman_functions
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.spynnaker_simulator_interface \
    import SpynnakerSimulatorInterface

# general imports
from six import add_metaclass
import logging
import math
import os

# global objects
logger = logging.getLogger(__name__)


@add_metaclass(AbstractBase)
class AbstractSpiNNakerCommon(AbstractSpinnakerBase,
                              SpynnakerSimulatorInterface):
    """ main interface for neural code

    """

    CONFIG_FILE_NAME = "spynnaker.cfg"

    _EXECUTABLE_FINDER = ExecutableFinder()

    def __init__(
            self, graph_label, database_socket_addresses, n_chips_required,
            timestep, max_delay, min_delay, hostname,
            user_extra_algorithm_xml_path=None, user_extra_mapping_inputs=None,
            user_extra_algorithms_pre_run=None, time_scale_factor=None,
            extra_post_run_algorithms=None, extra_mapping_algorithms=None,
            extra_load_algorithms=None):

        # Read config file
        config = conf_loader.load_config(spynnaker.pyNN, self.CONFIG_FILE_NAME)

        # add model binaries
        self._EXECUTABLE_FINDER.add_path(
            os.path.dirname(model_binaries.__file__))

        # pynn population objects
        self._populations = list()
        self._projections = list()
        self._edge_count = 0

        # the number of edges that are associated with commands being sent to
        # a vertex
        self._command_edge_count = 0
        self._live_spike_recorder = dict()

        # create xml path for where to locate spynnaker related functions when
        # using auto pause and resume
        extra_algorithm_xml_path = list()
        extra_algorithm_xml_path.append(os.path.join(
            os.path.dirname(overridden_pacman_functions.__file__),
            "algorithms_metadata.xml"))
        if user_extra_algorithm_xml_path is not None:
            extra_algorithm_xml_path.extend(user_extra_algorithm_xml_path)

        extra_mapping_inputs = dict()
        extra_mapping_inputs['CreateAtomToEventIdMapping'] = config.getboolean(
            "Database", "create_routing_info_to_neuron_id_mapping")

        if extra_mapping_algorithms is None:
            extra_mapping_algorithms = list()
        if extra_load_algorithms is None:
            extra_load_algorithms = list()
        if user_extra_mapping_inputs is not None:
            extra_mapping_inputs.update(user_extra_mapping_inputs)
        extra_algorithms_pre_run = list()

        if config.getboolean("Reports", "draw_network_graph"):
            extra_mapping_algorithms.append(
                "SpYNNakerConnectionHolderGenerator")
            extra_load_algorithms.append(
                "SpYNNakerNeuronGraphNetworkSpecificationReport")

        if config.getboolean("Reports", "reportsEnabled"):
            if config.getboolean("Reports", "writeSynapticReport"):
                extra_algorithms_pre_run.append("SynapticMatrixReport")
        if user_extra_algorithms_pre_run is not None:
            extra_algorithms_pre_run.extend(user_extra_algorithms_pre_run)

        # timing parameters
        self._min_delay = None
        self._max_delay = None

        self._neurons_per_core_set = set()

        AbstractSpinnakerBase.__init__(
            self, config,
            graph_label=graph_label,
            executable_finder=self._EXECUTABLE_FINDER,
            database_socket_addresses=database_socket_addresses,
            extra_algorithm_xml_paths=extra_algorithm_xml_path,
            extra_mapping_inputs=extra_mapping_inputs,
            n_chips_required=n_chips_required,
            extra_pre_run_algorithms=extra_algorithms_pre_run,
            extra_post_run_algorithms=extra_post_run_algorithms,
            extra_load_algorithms=extra_load_algorithms,
            extra_mapping_algorithms=extra_mapping_algorithms)

        # set up machine targeted data
        self._set_up_timings(
            timestep, min_delay, max_delay, config, time_scale_factor)
        self.set_up_machine_specifics(hostname)

        logger.info("Setting time scale factor to {}."
                    .format(self._time_scale_factor))

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds."
                    .format(self._machine_time_step))

    def _set_up_timings(
            self, timestep, min_delay, max_delay, config, time_scale_factor):

        if time_scale_factor is None:
            time_scale_factor = helpful_functions.read_config_int(
                config, "Machine", "timeScaleFactor")

        # deal with params allowed via the setup options
        if timestep is not None:

            # convert from milliseconds into microseconds
            try:
                if timestep <= 0:
                    raise InvalidParameterType(
                        "invalid timestamp {}: must greater than zero".format(
                            timestep))
                timestep *= 1000.0
                timestep = math.ceil(timestep)
            except (TypeError, AttributeError):
                raise InvalidParameterType(
                    "timestamp parameter must numerical")
            self._machine_time_step = timestep
        else:
            self._machine_time_step = config.getint(
                "Machine", "machineTimeStep")

        if (min_delay is not None and
                float(min_delay * 1000) < self._machine_time_step):
            raise common_exceptions.ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step".format(
                    constants.MIN_SUPPORTED_DELAY * self._machine_time_step))

        natively_supported_delay_for_models = \
            constants.MAX_SUPPORTED_DELAY_TICS
        delay_extension_max_supported_delay = (
            constants.MAX_DELAY_BLOCKS *
            constants.MAX_TIMER_TICS_SUPPORTED_PER_BLOCK)

        max_delay_tics_supported = \
            natively_supported_delay_for_models + \
            delay_extension_max_supported_delay

        if (max_delay is not None and
                float(max_delay * 1000.0) >
                (max_delay_tics_supported * self._machine_time_step)):
            raise common_exceptions.ConfigurationException(
                "Pacman does not support max delays above {} ms with the "
                "current machine time step".format(
                    0.144 * self._machine_time_step))
        if min_delay is not None:
            self._min_delay = min_delay
        else:
            self._min_delay = self._machine_time_step / 1000.0

        if max_delay is not None:
            self._max_delay = max_delay
        else:
            self._max_delay = (
                max_delay_tics_supported * (self._machine_time_step / 1000.0))

        if (config.has_option("Machine", "timeScaleFactor") and
                config.get("Machine", "timeScaleFactor") != "None"):
            self._time_scale_factor = \
                config.getint("Machine", "timeScaleFactor")
            if self._machine_time_step * self._time_scale_factor < 1000:
                if config.getboolean(
                        "Mode", "violate_1ms_wall_clock_restriction"):
                    logger.warn(
                        "****************************************************")
                    logger.warn(
                        "*** The combination of simulation time step and  ***")
                    logger.warn(
                        "*** the machine time scale factor results in a   ***")
                    logger.warn(
                        "*** wall clock timer tick that is currently not  ***")
                    logger.warn(
                        "*** reliably supported by the spinnaker machine. ***")
                    logger.warn(
                        "****************************************************")
                else:
                    raise common_exceptions.ConfigurationException(
                        "The combination of simulation time step and the"
                        " machine time scale factor results in a wall clock "
                        "timer tick that is currently not reliably supported "
                        "by the spinnaker machine.  If you would like to "
                        "override this behaviour (at your own risk), please "
                        "add violate_1ms_wall_clock_restriction = True to the "
                        "[Mode] section of your .{} file".format(
                            self.CONFIG_FILE_NAME))
        else:
            if time_scale_factor is not None:
                self._time_scale_factor = time_scale_factor
            else:
                self._time_scale_factor = max(
                    1, math.ceil(1000.0 / float(timestep)))
                if self._time_scale_factor > 1:
                    logger.warn(
                        "A timestep was entered that has forced sPyNNaker "
                        "to automatically slow the simulation down from "
                        "real time by a factor of {}. To remove this "
                        "automatic behaviour, please enter a "
                        "timescaleFactor value in your .{}".format(
                            self._time_scale_factor,
                            self.CONFIG_FILE_NAME))

    def _detect_if_graph_has_changed(self, reset_flags=True):
        """ Iterates though the graph and looks changes
        """
        changed = AbstractSpinnakerBase._detect_if_graph_has_changed(
            self, reset_flags)

        # Additionally check populations for changes
        for population in self._populations:
            if population.requires_mapping:
                changed = True
            if reset_flags:
                population.mark_no_changes()

        # Additionally check projections for changes
        for projection in self._projections:
            if projection.requires_mapping:
                changed = True
            if reset_flags:
                projection.mark_no_changes()

        return changed

    @property
    def min_delay(self):
        """ The minimum supported delay based in milliseconds
        """
        return self._min_delay

    @property
    def max_delay(self):
        """ The maximum supported delay based in milliseconds
        """
        return self._max_delay

    def add_application_vertex(self, vertex_to_add):
        if isinstance(vertex_to_add, CommandSender):
            self._command_sender = vertex_to_add

        self._application_graph.add_vertex(vertex_to_add)

    @staticmethod
    def _count_unique_keys(commands):
        unique_keys = {command.key for command in commands}
        return len(unique_keys)

    def add_population(self, population):
        """ Called by each population to add itself to the list
        """
        self._populations.append(population)

    def add_projection(self, projection):
        """ Called by each projection to add itself to the list
        """
        self._projections.append(projection)

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
        :rtype: None
        """
        for population in self._populations:
            population._end()

        AbstractSpinnakerBase.stop(
            self, turn_off_machine, clear_routing_tables, clear_tags)
        self.reset_number_of_neurons_per_core()
        globals_variables.unset_simulator()

    def run(self, run_time):
        """ Run the model created

        :param run_time: the time in ms to run the simulation for
        """

        # extra post run algorithms
        self._dsg_algorithm = "SpynnakerDataSpecificationWriter"
        for projection in self._projections:
            projection._clear_cache()
        AbstractSpinnakerBase.run(self, run_time)

    @property
    def time_scale_factor(self):
        """ the multiplicative scaling from application time to real
        execution time

        :return: the time scale factor
        """
        return self._time_scale_factor

    @staticmethod
    def register_binary_search_path(search_path):
        """ Registers an additional binary search path for executables
            :param search_path: absolute search path for binaries
            """
        AbstractSpiNNakerCommon._EXECUTABLE_FINDER.add_path(search_path)

    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        if hasattr(neuron_type, "set_model_max_atoms_per_core"):
            if hasattr(neuron_type, "get_max_atoms_per_core"):
                previous = neuron_type.get_max_atoms_per_core()
                if previous < max_permitted:
                    logger.warning(
                        "Attempt to increase number_of_neurons_per_core "
                        "from {} to {} ignored".format(previous,
                                                       max_permitted))
                    return
            neuron_type.set_model_max_atoms_per_core(max_permitted)
            self._neurons_per_core_set.add(neuron_type)
        else:
            raise Exception("{} is not a Vertex type".format(neuron_type))

    def reset_number_of_neurons_per_core(self):
        for neuron_type in self._neurons_per_core_set:
            neuron_type.set_model_max_atoms_per_core()

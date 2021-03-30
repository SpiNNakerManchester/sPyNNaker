# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import math
import os
from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.interface.abstract_spinnaker_base import (
    AbstractSpinnakerBase)
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utility_models import CommandSender
from spinn_front_end_common.utilities.utility_objs import ExecutableFinder
from spinn_front_end_common.utilities.globals_variables import unset_simulator
from spynnaker.pyNN import extra_algorithms, model_binaries
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.spynnaker_simulator_interface import (
    SpynnakerSimulatorInterface)
from spynnaker.pyNN.utilities.extracted_data import ExtractedData
from spynnaker import __version__ as version

logger = FormatAdapter(logging.getLogger(__name__))


class AbstractSpiNNakerCommon(
        AbstractSpinnakerBase, SpynnakerSimulatorInterface,
        metaclass=AbstractBase):
    """ Main interface for neural code.
    """
    __slots__ = [
        "__command_edge_count",
        "__edge_count",
        "__id_counter",
        "__live_spike_recorder",
        "__min_delay",
        "__max_delay",
        "__neurons_per_core_set",
        "_populations",
        "_projections"]

    __EXECUTABLE_FINDER = ExecutableFinder()

    CONFIG_FILE_NAME = "spynnaker.cfg"

    @classmethod
    def extended_config_path(cls):
        return os.path.join(os.path.dirname(__file__),
                            cls.CONFIG_FILE_NAME)

    def __init__(
            self, graph_label, database_socket_addresses, n_chips_required,
            n_boards_required, timestep, max_delay, min_delay, hostname,
            user_extra_algorithm_xml_path=None, user_extra_mapping_inputs=None,
            user_extra_algorithms_pre_run=None, time_scale_factor=None,
            extra_post_run_algorithms=None, extra_mapping_algorithms=None,
            extra_load_algorithms=None, front_end_versions=None):
        """
        :param str graph_label:
        :param database_socket_addresses:
        :type database_socket_addresses:
            iterable(~spinn_utilities.socket_address.SocketAddress)
        :param n_chips_required:
        :type n_chips_required: int or None
        :param n_boards_required:
        :type n_boards_required: int or None
        :param int timestep:
        :param float max_delay:
        :param float min_delay:
        :param str hostname:
        :param user_extra_algorithm_xml_path:
        :type user_extra_algorithm_xml_path: str or None
        :param user_extra_mapping_inputs:
        :type user_extra_mapping_inputs: dict(str, Any) or None
        :param user_extra_algorithms_pre_run:
        :type user_extra_algorithms_pre_run: list(str) or None
        :param time_scale_factor:
        :type time_scale_factor: float or None
        :param extra_post_run_algorithms:
        :type extra_post_run_algorithms: list(str) or None
        :param extra_mapping_algorithms:
        :type extra_mapping_algorithms: list(str) or None
        :param extra_load_algorithms:
        :type extra_load_algorithms: list(str) or None
        :param front_end_versions:
        :type front_end_versions: list(tuple(str,str)) or None
        """
        # pylint: disable=too-many-arguments, too-many-locals

        # add model binaries
        self.__EXECUTABLE_FINDER.add_path(
            os.path.dirname(model_binaries.__file__))

        # pynn population objects
        self._populations = []
        self._projections = []
        self.__edge_count = 0
        self.__id_counter = 0

        # the number of edges that are associated with commands being sent to
        # a vertex
        self.__command_edge_count = 0
        self.__live_spike_recorder = dict()

        # create XML path for where to locate sPyNNaker related functions when
        # using auto pause and resume
        extra_algorithm_xml_path = list()
        extra_algorithm_xml_path.append(os.path.join(
            os.path.dirname(extra_algorithms.__file__),
            "algorithms_metadata.xml"))
        if user_extra_algorithm_xml_path is not None:
            extra_algorithm_xml_path.extend(user_extra_algorithm_xml_path)

        # timing parameters
        self.__min_delay = None
        self.__max_delay = max_delay

        self.__neurons_per_core_set = set()

        versions = [("sPyNNaker", version)]
        if front_end_versions is not None:
            versions.extend(front_end_versions)

        super().__init__(
            configfile=self.CONFIG_FILE_NAME,
            executable_finder=self.__EXECUTABLE_FINDER,
            graph_label=graph_label,
            database_socket_addresses=database_socket_addresses,
            extra_algorithm_xml_paths=extra_algorithm_xml_path,
            n_chips_required=n_chips_required,
            n_boards_required=n_boards_required,
            default_config_paths=[self.extended_config_path()],
            front_end_versions=versions)

        # update inputs needed by the machine level calls.
        self.update_extra_inputs({'UserDefinedMaxDelay': self.__max_delay})

        extra_mapping_inputs = dict()
        extra_mapping_inputs['CreateAtomToEventIdMapping'] = \
            self.config.getboolean(
                "Database", "create_routing_info_to_neuron_id_mapping")
        extra_mapping_inputs["WriteBitFieldGeneratorIOBUF"] = \
            self.config.getboolean("Reports", "write_bit_field_iobuf")
        extra_mapping_inputs["GenerateBitFieldReport"] = \
            self.config.getboolean("Reports", "generate_bit_field_report")
        extra_mapping_inputs["GenerateBitFieldSummaryReport"] = \
            self.config.getboolean(
                "Reports", "generate_bit_field_summary_report")
        extra_mapping_inputs["SynapticExpanderReadIOBuf"] = \
            self.config.getboolean("Reports", "write_expander_iobuf")
        if user_extra_mapping_inputs is not None:
            extra_mapping_inputs.update(user_extra_mapping_inputs)

        if extra_mapping_algorithms is None:
            extra_mapping_algorithms = []
        if extra_load_algorithms is None:
            extra_load_algorithms = []
        if extra_post_run_algorithms is None:
            extra_post_run_algorithms = []
        extra_load_algorithms.append("SynapseExpander")
        extra_load_algorithms.append("OnChipBitFieldGenerator")
        extra_load_algorithms.append("FinishConnectionHolders")
        extra_algorithms_pre_run = []

        if self.config.getboolean("Reports", "draw_network_graph"):
            extra_mapping_algorithms.append(
                "SpYNNakerConnectionHolderGenerator")
            extra_mapping_algorithms.append(
                "PreAllocateForBitFieldRouterCompressor")
            extra_load_algorithms.append(
                "SpYNNakerNeuronGraphNetworkSpecificationReport")

        if self.config.getboolean("Reports", "reports_enabled"):
            if self.config.getboolean("Reports", "write_synaptic_report"):
                extra_algorithms_pre_run.append("SynapticMatrixReport")
        if user_extra_algorithms_pre_run is not None:
            extra_algorithms_pre_run.extend(user_extra_algorithms_pre_run)

        self.update_extra_mapping_inputs(extra_mapping_inputs)
        self.extend_extra_mapping_algorithms(extra_mapping_algorithms)
        self.prepend_extra_pre_run_algorithms(extra_algorithms_pre_run)
        self.extend_extra_post_run_algorithms(extra_post_run_algorithms)
        self.extend_extra_load_algorithms(extra_load_algorithms)

        # set up machine targeted data
        self._set_up_timings(
            timestep, min_delay, self.config, time_scale_factor)
        self.set_up_machine_specifics(hostname)

        logger.info("Setting time scale factor to {}.",
                    self.time_scale_factor)

        # get the machine time step
        logger.info("Setting machine time step to {} micro-seconds.",
                    self.machine_time_step)

    def _set_up_timings(self, timestep, min_delay, config, time_scale_factor):
        """
        :param float timestep:
        :param int min_delay:
        :param configparser.ConfigParser config:
        :param float time_scale_factor:
        """

        # Get the standard values
        if timestep is None:
            self.set_up_timings(timestep, time_scale_factor)
        else:
            self.set_up_timings(
                math.ceil(timestep * MICRO_TO_MILLISECOND_CONVERSION),
                time_scale_factor)

        # Sort out the minimum delay
        if (min_delay is not None and
                (min_delay * MICRO_TO_MILLISECOND_CONVERSION) <
                self.machine_time_step):
            raise ConfigurationException(
                "Pacman does not support min delays below {} ms with the "
                "current machine time step".format(
                    constants.MIN_SUPPORTED_DELAY * self.machine_time_step))
        if min_delay is not None:
            self.__min_delay = min_delay
        else:
            self.__min_delay = (
                self.machine_time_step / MICRO_TO_MILLISECOND_CONVERSION)

        # Sort out the time scale factor if not user specified
        # (including config)
        if self.time_scale_factor is None:
            self.time_scale_factor = max(
                1.0, math.ceil(
                    MICRO_TO_MILLISECOND_CONVERSION / self.machine_time_step))
            if self.time_scale_factor > 1:
                logger.warning(
                    "A timestep was entered that has forced sPyNNaker to "
                    "automatically slow the simulation down from real time "
                    "by a factor of {}. To remove this automatic behaviour, "
                    "please enter a timescaleFactor value in your .{}",
                    self.time_scale_factor, self.CONFIG_FILE_NAME)

        # Check the combination of machine time step and time scale factor
        if (self.machine_time_step * self.time_scale_factor <
                MICRO_TO_MILLISECOND_CONVERSION):
            if not config.getboolean(
                    "Mode", "violate_1ms_wall_clock_restriction"):
                raise ConfigurationException(
                    "The combination of simulation time step and the machine "
                    "time scale factor results in a wall clock timer tick "
                    "that is currently not reliably supported by the"
                    "SpiNNaker machine.  If you would like to override this"
                    "behaviour (at your own risk), please add "
                    "violate_1ms_wall_clock_restriction = True to the [Mode] "
                    "section of your .{} file".format(self.CONFIG_FILE_NAME))
            logger.warning(
                "****************************************************")
            logger.warning(
                "*** The combination of simulation time step and  ***")
            logger.warning(
                "*** the machine time scale factor results in a   ***")
            logger.warning(
                "*** wall clock timer tick that is currently not  ***")
            logger.warning(
                "*** reliably supported by the SpiNNaker machine. ***")
            logger.warning(
                "****************************************************")

    def _detect_if_graph_has_changed(self, reset_flags=True):
        """ Iterate though the graph and look for changes.

        :param bool reset_flags:
        """
        changed, data_changed = super()._detect_if_graph_has_changed(
            reset_flags)

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

        return changed, data_changed

    @property
    def min_delay(self):
        """ The minimum supported delay, in milliseconds.
        """
        return self.__min_delay

    def add_application_vertex(self, vertex):
        if isinstance(vertex, CommandSender):
            self._command_sender = vertex
        super().add_application_vertex(vertex)

    @staticmethod
    def _count_unique_keys(commands):
        unique_keys = {command.key for command in commands}
        return len(unique_keys)

    def add_population(self, population):
        """ Called by each population to add itself to the list.
        """
        self._populations.append(population)

    def add_projection(self, projection):
        """ Called by each projection to add itself to the list.
        """
        self._projections.append(projection)

    def stop(self, turn_off_machine=None, clear_routing_tables=None,
             clear_tags=None):
        """
        :param turn_off_machine: decides if the machine should be powered down
            after running the execution. Note that this powers down all boards
            connected to the BMP connections given to the transceiver
        :type turn_off_machine: bool or None
        :param clear_routing_tables: informs the tool chain if it
            should turn off the clearing of the routing tables
        :type clear_routing_tables: bool or None
        :param clear_tags: informs the tool chain if it should clear the tags
            off the machine at stop
        :type clear_tags: bool or None
        :rtype: None
        """
        # pylint: disable=protected-access
        for population in self._populations:
            population._end()

        super().stop(turn_off_machine, clear_routing_tables, clear_tags)
        self.reset_number_of_neurons_per_core()
        unset_simulator(self)

    def run(self, run_time, sync_time=0.0):
        """ Run the model created.

        :param run_time: the time (in milliseconds) to run the simulation for
        :type run_time: float or int
        :param float sync_time:
            If not 0, this specifies that the simulation should pause after
            this duration.  The continue_simulation() method must then be
            called for the simulation to continue.
        :rtype: None
        """
        # pylint: disable=protected-access

        # extra post run algorithms
        self._dsg_algorithm = "SpynnakerDataSpecificationWriter"
        for projection in self._projections:
            projection._clear_cache()

        if (self.config.getboolean("Reports", "reports_enabled") and
                self.config.getboolean(
                    "Reports", "write_redundant_packet_count_report") and
                not self._use_virtual_board and run_time is not None and
                not self._has_ran and self._config.getboolean(
                    "Reports", "writeProvenanceData")):
            self.extend_extra_post_run_algorithms(
                ["RedundantPacketCountReport"])

        super().run(run_time, sync_time)
        for projection in self._projections:
            projection._clear_cache()

    @staticmethod
    def register_binary_search_path(search_path):
        """ Register an additional binary search path for executables.

        :param str search_path: absolute search path for binaries
        :rtype: None
        """
        # pylint: disable=protected-access
        AbstractSpiNNakerCommon.__EXECUTABLE_FINDER.add_path(search_path)

    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        if not hasattr(neuron_type, "set_model_max_atoms_per_core"):
            raise Exception("{} is not a Vertex type".format(neuron_type))

        if hasattr(neuron_type, "get_max_atoms_per_core"):
            previous = neuron_type.get_max_atoms_per_core()
            if previous < max_permitted:
                logger.warning(
                    "Attempt to increase number_of_neurons_per_core "
                    "from {} to {} ignored", previous, max_permitted)
                return
        neuron_type.set_model_max_atoms_per_core(max_permitted)
        self.__neurons_per_core_set.add(neuron_type)

    def reset_number_of_neurons_per_core(self):
        for neuron_type in self.__neurons_per_core_set:
            neuron_type.set_model_max_atoms_per_core()

    def get_projections_data(self, projection_to_attribute_map):
        """ Common data extractor for projection data. Allows fully
            exploitation of the ????

        :param projection_to_attribute_map:
            the projection to attributes mapping
        :type projection_to_attribute_map:
            dict(~spynnaker.pyNN.models.projection.Projection,
            list(int) or tuple(int) or None)
        :return: a extracted data object with get method for getting the data
        :rtype: ExtractedData
        """
        # pylint: disable=protected-access

        # build data structure for holding data
        mother_lode = ExtractedData()

        # acquire data objects from front end
        using_monitors = self._last_run_outputs["UsingAdvancedMonitorSupport"]

        # if using extra monitor functionality, locate extra data items
        receivers = list()
        if using_monitors:
            receivers = self._locate_receivers_from_projections(
                projection_to_attribute_map.keys(),
                self.get_generated_output(
                    "MemoryMCGatherVertexToEthernetConnectedChipMapping"),
                self.get_generated_output(
                    "MemoryExtraMonitorToChipMapping"))

        # set up the router timeouts to stop packet loss
        for data_receiver, extra_monitor_cores in receivers:
            data_receiver.load_system_routing_tables(
                self._txrx,
                self.get_generated_output("MemoryExtraMonitorVertices"),
                self._placements)
            data_receiver.set_cores_for_data_streaming(
                self._txrx, list(extra_monitor_cores), self._placements)

        # acquire the data
        for projection in projection_to_attribute_map:
            for attribute in projection_to_attribute_map[projection]:
                data = projection._get_synaptic_data(
                    as_list=True, data_to_get=attribute,
                    fixed_values=None, notify=None,
                    handle_time_out_configuration=False)
                mother_lode.set(projection, attribute, data)

        # reset time outs for the receivers
        for data_receiver, extra_monitor_cores in receivers:
            data_receiver.unset_cores_for_data_streaming(
                self._txrx, list(extra_monitor_cores), self._placements)
            data_receiver.load_application_routing_tables(
                self._txrx,
                self.get_generated_output("MemoryExtraMonitorVertices"),
                self._placements)

        # return data items
        return mother_lode

    def _locate_receivers_from_projections(
            self, projections, gatherers, extra_monitors_per_chip):
        """ Locate receivers and their corresponding monitor cores for\
            setting router time-outs.

        :param list projections: the projections going to be read
        :param gatherers: the gatherers per Ethernet chip
        :param extra_monitors_per_chip: the extra monitor cores per chip
        :return: list of tuples with gatherer and its extra monitor cores
        :rtype: list
        """
        # pylint: disable=protected-access
        important_gathers = set()

        # iterate though projections
        for projection in projections:
            # iteration though the projections machine edges to locate chips
            for edge in projection._projection_edge.machine_edges:
                placement = self._placements.get_placement_of_vertex(
                    edge.post_vertex)
                chip = self._machine.get_chip_at(placement.x, placement.y)

                # locate extra monitor cores on the board of this chip
                extra_monitor_cores_on_board = set(
                    extra_monitors_per_chip[xy]
                    for xy in self._machine.get_existing_xys_on_board(chip))

                # map gatherer to extra monitor cores for board
                important_gathers.add((
                    gatherers[(chip.nearest_ethernet_x,
                               chip.nearest_ethernet_y)],
                    frozenset(extra_monitor_cores_on_board)))
        return list(important_gathers)

    @property
    def id_counter(self):
        """ The id_counter, currently used by the populations.

        .. note::
            Maybe it could live in the pop class???

        :rtype: int
        """
        return self.__id_counter

    @id_counter.setter
    def id_counter(self, new_value):
        """ Setter for id_counter, currently used by the populations.

        .. note::
            Maybe it could live in the pop class???

        :param int new_value: new value for id_counter
        """
        self.__id_counter = new_value

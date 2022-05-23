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
from lazyarray import __version__ as lazyarray_version
from quantities import __version__ as quantities_version
import math
from neo import __version__ as neo_version
import os
from pyNN.common import control as pynn_control
from pyNN import __version__ as pynn_version

from spinn_utilities.log import FormatAdapter
from spinn_utilities.config_holder import get_config_bool, get_config_str
from spinn_utilities.overrides import overrides

from spinn_front_end_common.interface.abstract_spinnaker_base import (
    AbstractSpinnakerBase)
from spinn_front_end_common.interface.provenance import (
    DATA_GENERATION, LOADING, MAPPING, ProvenanceWriter, RUN_LOOP)
from spinn_front_end_common.utilities import FecTimer
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utility_models import CommandSender
from spinn_front_end_common.utilities.utility_objs import ExecutableFinder

from spynnaker import _version
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.config_setup import CONFIG_FILE_NAME, setup_configs
from spynnaker.pyNN.extra_algorithms import (
    delay_support_adder, on_chip_bitfield_generator,
    redundant_packet_count_report,
    spynnaker_data_specification_writer,
    spynnaker_neuron_graph_network_specification_report)
from spynnaker.pyNN.extra_algorithms.\
    spynnaker_machine_bit_field_router_compressor import (
        spynnaker_machine_bitfield_ordered_covering_compressor,
        spynnaker_machine_bitField_pair_router_compressor)
from spynnaker.pyNN.extra_algorithms.connection_holder_finisher import (
    finish_connection_holders)
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    spynnaker_splitter_partitioner, spynnaker_splitter_selector)
from spynnaker.pyNN.extra_algorithms.synapse_expander import synapse_expander
from spynnaker.pyNN.utilities import constants

logger = FormatAdapter(logging.getLogger(__name__))

_NAME = "SpiNNaker_under_version({}-{})".format(
    _version.__version__, _version.__version_name__)


class SpiNNaker(AbstractSpinnakerBase, pynn_control.BaseState):
    """ Main interface for the sPyNNaker implementation of PyNN 0.8/0.9
    """

    __slots__ = [
        "__id_counter",
        "__min_delay",
        "__neurons_per_core_set",
        "_populations",
        "_projections"]

    __EXECUTABLE_FINDER = ExecutableFinder()

    def __init__(
            self, database_socket_addresses,
            time_scale_factor, min_delay, graph_label,
            n_chips_required=None, n_boards_required=None, timestep=0.1):
        # pylint: disable=too-many-arguments, too-many-locals

        # change min delay auto to be the min delay supported by simulator
        if min_delay == "auto":
            min_delay = timestep

        # population and projection holders
        self._populations = list()
        self._projections = list()

        # pynn demanded objects
        self.__segment_counter = 0
        self.__recorders = set([])

        # main pynn interface inheritance
        pynn_control.BaseState.__init__(self)

        # SpiNNaker setup
        setup_configs()

        # add model binaries
        self.__EXECUTABLE_FINDER.add_path(
            os.path.dirname(model_binaries.__file__))

        # pynn population objects
        self._populations = []
        self._projections = []
        self.__id_counter = 0

        # timing parameters
        self.__min_delay = None

        self.__neurons_per_core_set = set()

        super().__init__(
            executable_finder=self.__EXECUTABLE_FINDER,
            graph_label=graph_label,
            database_socket_addresses=database_socket_addresses,
            n_chips_required=n_chips_required,
            n_boards_required=n_boards_required)

        # set up machine targeted data
        self._set_up_timings(timestep, min_delay, time_scale_factor)
        self.check_machine_specifics()

        logger.info(f'Setting time scale factor to '
                    f'{self.time_scale_factor}.')

        # get the machine time step
        logger.info(f'Setting machine time step to '
                    f'{self.machine_time_step} '
                    f'micro-seconds.')

        with ProvenanceWriter() as db:
            db.insert_version("sPyNNaker_version", _version.__version__)
            db.insert_version("pyNN_version", pynn_version)
            db.insert_version("quantities_version", quantities_version)
            db.insert_version("neo_version", neo_version)
            db.insert_version("lazyarray_version", lazyarray_version)

    def _clear_and_run(self, run_time, sync_time=0.0):
        """ Clears the projections and Run the model created.

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
        for projection in self._projections:
            projection._clear_cache()

        super(SpiNNaker, self).run(run_time, sync_time)
        for projection in self._projections:
            projection._clear_cache()

    def run(self, run_time, sync_time=0.0):
        """ Run the simulation for a span of simulation time.
        :param run_time: the time to run for, in milliseconds
        :return: None
        """
        self._clear_and_run(run_time, sync_time)

    def run_until(self, tstop):
        """ Run the simulation until the given simulation time.

        :param tstop: when to run until in milliseconds
        """
        # Build data
        self._clear_and_run(tstop - self.t)

    def clear(self):
        """ Clear the current recordings and reset the simulation
        """
        self.recorders = set([])
        self.id_counter = 0
        self.__segment_counter = -1
        self.reset()

        # Stop any currently running SpiNNaker application
        self.stop()

    def reset(self):
        """ Reset the state of the current network to time t = 0.
        """
        for population in self._populations:
            population._cache_data()

        self.__segment_counter += 1

        # Call superclass implementation
        AbstractSpinnakerBase.reset(self)

    @property
    def state(self):
        """ Used to bypass the dual level object

        :return: the SpiNNaker object
        :rtype: ~spynnaker8.spinnaker.SpiNNaker
        """
        return self

    @property
    def mpi_rank(self):
        """ Gets the MPI rank of the simulator

        .. note::
            Meaningless on SpiNNaker, so we pretend we're the head node.

        :return: Constant: 0
        :rtype: int
        """
        return 0

    @mpi_rank.setter
    def mpi_rank(self, new_value):
        """ sPyNNaker does not use this value meaningfully

        :param new_value: Ignored
        """

    @property
    def num_processes(self):
        """ Gets the number of MPI worker processes

        .. note::
            Meaningless on SpiNNaker, so we pretend there's one MPI process

        :return: Constant: 1
        :rtype: int
        """
        return 1

    @num_processes.setter
    def num_processes(self, new_value):
        """ sPyNNaker does not use this value meaningfully

        :param new_value: Ignored
        """

    @property
    def dt(self):
        """ The machine time step in milliseconds

        :return: the machine time step
        :rtype: float
        """
        return self.machine_time_step_ms

    @dt.setter
    def dt(self, new_value):
        """ The machine time step in milliseconds

        :param float new_value: new value for machine time step in microseconds
        """
        self.machine_time_step = new_value * MICRO_TO_MILLISECOND_CONVERSION

    @property
    def t(self):
        """ The current simulation time in milliseconds

        :return: the current runtime already executed
        :rtype: float
        """
        return self._current_run_timesteps * self.machine_time_step_ms

    @property
    def segment_counter(self):
        """ The number of the current recording segment being generated.

        :return: the segment counter
        :rtype: int
        """
        return self.__segment_counter

    @segment_counter.setter
    def segment_counter(self, new_value):
        """ The number of the current recording segment being generated.

        :param int new_value: new value for the segment counter
        """
        self.__segment_counter = new_value

    @property
    def running(self):
        """ Whether the simulation is running or has run.

        .. note::
            Ties into our has_ran parameter for automatic pause and resume.

        :return: the has_ran variable from the SpiNNaker main interface
        :rtype: bool
        """
        return self._has_ran

    @running.setter
    def running(self, new_value):
        """ Setter for the has_ran parameter, only used by the PyNN interface,\
            supports tracking where it thinks its setting this parameter.

        :param bool new_value: the new value for the simulation
        """
        self._has_ran = new_value

    @property
    def name(self):
        """ The name of the simulator. Used to ensure PyNN recording neo\
            blocks are correctly labelled.

        :return: the name of the simulator.
        :rtype: str
        """
        return _NAME

    @property
    def populations(self):
        """ The list of all populations in the simulation.

        :return: list of populations
        :rtype: list(~spynnaker.pyNN.models.population.Population)
        """
        # needed by the population class
        return self._populations

    @property
    def projections(self):
        """ The list of all projections in the simulation.

        :return: list of projections
        :rtype: list(~spynnaker.pyNN.models.projection.Projection)
        """
        # needed by the projection class.
        return self._projections

    @property
    def recorders(self):
        """ The recorders, used by the PyNN state object

        :return: the internal recorders object
        :rtype: list(~spynnaker.pyNN.models.recorder.Recorder)
        """
        return self.__recorders

    @recorders.setter
    def recorders(self, new_value):
        """ Setter for the internal recorders object

        :param new_value: the new value for the recorder
        """
        self.__recorders = new_value

    def _set_up_timings(self, timestep, min_delay, time_scale_factor):
        """
        :param timestep: machine_time_Step in milli seconds
        :type timestep: float or None
        :tpye min_delay: int or None
        :type time_scale_factor: int or None
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
                min_delay < self.machine_time_step_ms):
            raise ConfigurationException(
                f"Pacman does not support min delays below "
                f"{constants.MIN_SUPPORTED_DELAY * self.machine_time_step} "
                f"ms with the current machine time step")
        if min_delay is not None:
            self.__min_delay = min_delay
        else:
            self.__min_delay = self.machine_time_step_ms

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
                    self.time_scale_factor, CONFIG_FILE_NAME)

        # Check the combination of machine time step and time scale factor
        if (self.machine_time_step_ms * self.time_scale_factor < 1):
            if not get_config_bool(
                    "Mode", "violate_1ms_wall_clock_restriction"):
                raise ConfigurationException(
                    "The combination of simulation time step and the machine "
                    "time scale factor results in a wall clock timer tick "
                    "that is currently not reliably supported by the"
                    "SpiNNaker machine.  If you would like to override this"
                    "behaviour (at your own risk), please add "
                    "violate_1ms_wall_clock_restriction = True to the [Mode] "
                    "section of your .{} file".format(CONFIG_FILE_NAME))
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
            raise NotImplementedError(
                "Please contact spinnker team as adding a CommandSender "
                "currently disabled")
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

    def stop(self):
        """
        :rtype: None
        """
        # pylint: disable=protected-access
        for population in self._populations:
            population._end()

        super().stop()
        self.reset_number_of_neurons_per_core()

    @staticmethod
    def register_binary_search_path(search_path):
        """ Register an additional binary search path for executables.

        :param str search_path: absolute search path for binaries
        :rtype: None
        """
        # pylint: disable=protected-access
        SpiNNaker.__EXECUTABLE_FINDER.add_path(search_path)

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

    @overrides(AbstractSpinnakerBase._execute_graph_data_specification_writer)
    def _execute_graph_data_specification_writer(self):
        with FecTimer(DATA_GENERATION, "Spynnaker data specification writer"):
            self._dsg_targets = spynnaker_data_specification_writer(
                self._placements, self._ipaddress, self._machine,
                self._app_id, self._max_run_time_steps)

    def _execute_spynnaker_ordered_covering_compressor(self):
        with FecTimer(
                LOADING,
                "Spynnaker machine bitfield ordered covering compressor") \
                as timer:
            if timer.skip_if_virtual_board():
                return
            spynnaker_machine_bitfield_ordered_covering_compressor(
                self._router_tables, self._txrx, self._machine, self._app_id,
                self._machine_graph, self._placements, self._executable_finder,
                self._routing_infos, self._executable_targets,
                get_config_bool("Reports", "write_expander_iobuf"))
            self._multicast_routes_loaded = True
            return None

    def _execute_spynnaker_pair_compressor(self):
        with FecTimer(
                LOADING, "Spynnaker machine bitfield pair router compressor") \
                as timer:
            if timer.skip_if_virtual_board():
                return
            spynnaker_machine_bitField_pair_router_compressor(
                self._router_tables, self._txrx, self._machine, self._app_id,
                self._machine_graph, self._placements, self._executable_finder,
                self._routing_infos, self._executable_targets,
                get_config_bool("Reports", "write_expander_iobuf"))
            self._multicast_routes_loaded = True
            return None

    @overrides(AbstractSpinnakerBase._do_delayed_compression)
    def _do_delayed_compression(self, name, compressed):
        if name == "SpynnakerMachineBitFieldOrderedCoveringCompressor":
            return self._execute_spynnaker_ordered_covering_compressor()

        if name == "SpynnakerMachineBitFieldPairRouterCompressor":
            return self._execute_spynnaker_pair_compressor()

        return AbstractSpinnakerBase._do_delayed_compression(
            self, name, compressed)

    def _execute_synapse_expander(self):
        with FecTimer(LOADING, "Synapse expander") as timer:
            if timer.skip_if_virtual_board():
                return
            synapse_expander(
                self.placements, self._txrx, self._executable_finder,
                get_config_bool("Reports", "write_expander_iobuf"))

    def _execute_on_chip_bit_field_generator(self):
        with FecTimer(LOADING, "Execute on chip bitfield generator") as timer:
            if timer.skip_if_virtual_board():
                return
            on_chip_bitfield_generator(
                self.placements, self.application_graph,
                self._executable_finder,  self._txrx, self._machine_graph)

    def _execute_finish_connection_holders(self):
        with FecTimer(LOADING, "Finish connection holders"):
            finish_connection_holders(self.application_graph)

    @overrides(AbstractSpinnakerBase._do_extra_load_algorithms)
    def _do_extra_load_algorithms(self):
        self._execute_synapse_expander()
        self._execute_on_chip_bit_field_generator()
        self._execute_finish_connection_holders()

    def _execute_write_network_graph(self):
        with FecTimer(
                MAPPING,
                "SpYNNakerNeuronGraphNetworkSpecificationReport") as timer:
            if timer.skip_if_cfg_false("Reports", "write_network_graph"):
                return
            spynnaker_neuron_graph_network_specification_report(
                self._application_graph)

    @overrides(AbstractSpinnakerBase._do_extra_mapping_algorithms,
               extend_doc=False)
    def _do_extra_mapping_algorithms(self):
        self._execute_write_network_graph()

    @overrides(AbstractSpinnakerBase._do_provenance_reports)
    def _do_provenance_reports(self):
        AbstractSpinnakerBase._do_provenance_reports(self)
        self._report_redundant_packet_count()

    def _report_redundant_packet_count(self):
        with FecTimer(RUN_LOOP, "Redundant packet count report") as timer:
            if timer.skip_if_cfg_false(
                    "Reports", "write_redundant_packet_count_report"):
                return
            redundant_packet_count_report()

    @overrides(AbstractSpinnakerBase._execute_splitter_selector)
    def _execute_splitter_selector(self):
        with FecTimer(MAPPING, "Spynnaker splitter selector"):
            spynnaker_splitter_selector(self._application_graph)

    @overrides(AbstractSpinnakerBase._execute_delay_support_adder,
               extend_doc=False)
    def _execute_delay_support_adder(self):
        """
        Runs, times and logs the DelaySupportAdder if required
        """
        name = get_config_str("Mapping", "delay_support_adder")
        if name is None:
            return
        with FecTimer(MAPPING, "DelaySupportAdder"):
            if name == "DelaySupportAdder":
                delay_support_adder(self._application_graph)
                return
            raise ConfigurationException(
                f"Unexpected cfg setting delay_support_adder: {name}")

    @overrides(AbstractSpinnakerBase._execute_splitter_partitioner)
    def _execute_splitter_partitioner(self, pre_allocated_resources):
        if not self._application_graph.n_vertices:
            return
        with FecTimer(MAPPING,  "SpynnakerSplitterPartitioner"):
            if self._machine:
                machine = self._machine
            else:
                machine = self._max_machine
            self._machine_graph, self._n_chips_needed = \
                spynnaker_splitter_partitioner(
                    self._application_graph, machine, self._plan_n_timesteps,
                    pre_allocated_resources)

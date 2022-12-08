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
    FecTimer, ProvenanceWriter, TimerCategory, TimerWork)
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker import _version
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.config_setup import CONFIG_FILE_NAME, setup_configs
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter
from spynnaker.pyNN.extra_algorithms import (
    delay_support_adder, neuron_expander, synapse_expander,
    redundant_packet_count_report,
    spynnaker_neuron_graph_network_specification_report)
from spynnaker.pyNN.extra_algorithms.\
    spynnaker_machine_bit_field_router_compressor import (
        spynnaker_machine_bitfield_ordered_covering_compressor,
        spynnaker_machine_bitField_pair_router_compressor)
from spynnaker.pyNN.extra_algorithms.connection_holder_finisher import (
    finish_connection_holders)
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    spynnaker_splitter_partitioner, spynnaker_splitter_selector)
from spynnaker.pyNN.utilities import constants

logger = FormatAdapter(logging.getLogger(__name__))


class SpiNNaker(AbstractSpinnakerBase, pynn_control.BaseState):
    """ Main interface for the sPyNNaker implementation of PyNN 0.8/0.9
    """

    __slots__ = []

    def __init__(
            self, time_scale_factor, min_delay,
            n_chips_required=None, n_boards_required=None, timestep=0.1):
        """

        :param time_scale_factor:
            multiplicative factor to the machine time step
            (does not affect the neuron models accuracy)
        :type time_scale_factor: int or None
        :param min_delay:
        :param n_chips_required:
            Deprecated! Use n_boards_required instead.
            Must be None if n_boards_required specified.
        :type n_chips_required: int or None
        :param n_boards_required:
            if you need to be allocated a machine (for spalloc) before
            building your graph, then fill this in with a general idea of
            the number of boards you need so that the spalloc system can
            allocate you a machine big enough for your needs.
        :type n_boards_required: int or None
        :param timestep:
            the time step of the simulations in micro seconds
            if None the cfg value is used
        :type timestep: float or None
        """
        # pylint: disable=too-many-arguments, too-many-locals

        # change min delay auto to be the min delay supported by simulator
        if min_delay == "auto":
            min_delay = timestep

        # pynn demanded objects
        self.__recorders = set([])

        # main pynn interface inheritance
        pynn_control.BaseState.__init__(self)

        # SpiNNaker setup
        setup_configs()

        # add model binaries
        # called before super.init as that logs the paths
        SpynnakerDataView.register_binary_search_path(
            os.path.dirname(model_binaries.__file__))

        super().__init__(
            data_writer_cls=SpynnakerDataWriter)

        self._data_writer.set_n_required(n_boards_required, n_chips_required)
        # set up machine targeted data
        self._set_up_timings(timestep, min_delay, time_scale_factor)

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

        # extra post prerun algorithms
        for projection in self._data_writer.iterate_projections():
            projection._clear_cache()

        super(SpiNNaker, self).run(run_time, sync_time)
        # extra post run algorithms
        for projection in self._data_writer.iterate_projections():
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
        self.reset()

        # Stop any currently running SpiNNaker application
        self.stop()

    def reset(self):
        """ Reset the state of the current network to time t = 0.
        """
        if not self._data_writer.is_ran_last():
            if not self._data_writer.is_ran_ever():
                logger.error("Ignoring the reset before the run")
            else:
                logger.error("Ignoring the repeated reset call")
            return
        for population in self._data_writer.iterate_populations():
            population._cache_data()  # pylint: disable=protected-access

        # Call superclass implementation
        AbstractSpinnakerBase.reset(self)

    @property
    def state(self):
        """ Used to bypass the dual level object

        :return: the SpiNNaker object
        :rtype: ~spynnaker.pyNN.SpiNNaker
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
        """ The simulation time step in milliseconds

        :return: the machine time step
        :rtype: float
        """
        return self._data_writer.get_simulation_time_step_ms()

    @dt.setter
    def dt(self, _):
        """ We do not support setting dt/ time step except during setup

        :raises NotImplementedError
        """
        raise NotImplementedError(
            "We do not support setting dt/ time step except during setup")

    @property
    def t(self):
        """ The current simulation time in milliseconds

        :return: the current runtime already executed
        :rtype: float
        """
        return self._data_writer.get_current_run_time_ms()

    @property
    def segment_counter(self):
        """ The number of the current recording segment being generated.

        :return: the segment counter
        :rtype: int
        """
        return self._data_writer.get_segment_counter()

    @segment_counter.setter
    def segment_counter(self, _):
        """ We do not support externally altering the segment counter

        raises: NotImplementedError
        """
        raise NotImplementedError(
            "We do not support externally altering the segment counter")

    @property
    def name(self):
        """ The name of the simulator. Used to ensure PyNN recording neo\
            blocks are correctly labelled.

        :return: the name of the simulator.
        :rtype: str
        """
        return _version._NAME  # pylint: disable=protected-access

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
            self._data_writer.set_up_timings_and_delay(
                timestep, time_scale_factor, min_delay)
        else:
            self._data_writer.set_up_timings_and_delay(
                math.ceil(timestep * MICRO_TO_MILLISECOND_CONVERSION),
                time_scale_factor, min_delay)

        # Check the combination of machine time step and time scale factor
        if (self._data_writer.get_simulation_time_step_ms() *
                self._data_writer.get_time_scale_factor() < 1):
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

    @staticmethod
    def _count_unique_keys(commands):
        unique_keys = {command.key for command in commands}
        return len(unique_keys)

    def stop(self):
        """
        :rtype: None
        """
        # pylint: disable=protected-access
        FecTimer.start_category(TimerCategory.SHUTTING_DOWN)
        for population in self._data_writer.iterate_populations():
            population._end()

        super().stop()

    def _execute_spynnaker_ordered_covering_compressor(self):
        with FecTimer("Spynnaker machine bitfield ordered covering compressor",
                      TimerWork.COMPRESSING) as timer:
            if timer.skip_if_virtual_board():
                return
            spynnaker_machine_bitfield_ordered_covering_compressor()
            # pylint: disable=attribute-defined-outside-init
            self._multicast_routes_loaded = True
            return None

    def _execute_spynnaker_pair_compressor(self):
        with FecTimer(
                "Spynnaker machine bitfield pair router compressor",
                TimerWork.COMPRESSING) as timer:
            if timer.skip_if_virtual_board():
                return
            spynnaker_machine_bitField_pair_router_compressor()
            # pylint: disable=attribute-defined-outside-init
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
        with FecTimer("Synapse expander", TimerWork.SYNAPSE) as timer:
            if timer.skip_if_virtual_board():
                return
            synapse_expander()

    def _execute_neuron_expander(self):
        with FecTimer("Neuron expander", TimerWork.SYNAPSE) as timer:
            if timer.skip_if_virtual_board():
                return
            neuron_expander()

    def _execute_finish_connection_holders(self):
        with FecTimer("Finish connection holders", TimerWork.OTHER):
            finish_connection_holders()

    @overrides(AbstractSpinnakerBase._do_extra_load_algorithms)
    def _do_extra_load_algorithms(self):
        self._execute_neuron_expander()
        self._execute_synapse_expander()
        self._execute_finish_connection_holders()

    def _report_write_network_graph(self):
        with FecTimer("SpYNNakerNeuronGraphNetworkSpecificationReport",
                      TimerWork.REPORT) as timer:
            if timer.skip_if_cfg_false("Reports", "write_network_graph"):
                return
            spynnaker_neuron_graph_network_specification_report()

    @overrides(AbstractSpinnakerBase._do_extra_mapping_algorithms,
               extend_doc=False)
    def _do_extra_mapping_algorithms(self):
        self._report_write_network_graph()

    @overrides(AbstractSpinnakerBase._do_provenance_reports)
    def _do_provenance_reports(self):
        AbstractSpinnakerBase._do_provenance_reports(self)
        self._report_redundant_packet_count()

    def _report_redundant_packet_count(self):
        with FecTimer("Redundant packet count report",
                      TimerWork.REPORT) as timer:
            if timer.skip_if_cfg_false(
                    "Reports", "write_redundant_packet_count_report"):
                return
            redundant_packet_count_report()

    @overrides(AbstractSpinnakerBase._execute_splitter_selector)
    def _execute_splitter_selector(self):
        with FecTimer("Spynnaker splitter selector", TimerWork.OTHER):
            spynnaker_splitter_selector()

    @overrides(AbstractSpinnakerBase._execute_delay_support_adder,
               extend_doc=False)
    def _execute_delay_support_adder(self):
        """
        Runs, times and logs the DelaySupportAdder if required
        """
        name = get_config_str("Mapping", "delay_support_adder")
        if name is None:
            return
        with FecTimer("DelaySupportAdder", TimerWork.OTHER):
            if name == "DelaySupportAdder":
                d_vertices, d_edges = delay_support_adder()
                for vertex in d_vertices:
                    self._data_writer.add_vertex(vertex)
                for edge in d_edges:
                    self._data_writer.add_edge(
                        edge, constants.SPIKE_PARTITION_ID)
                return
            raise ConfigurationException(
                f"Unexpected cfg setting delay_support_adder: {name}")

    @overrides(AbstractSpinnakerBase._execute_splitter_partitioner)
    def _execute_splitter_partitioner(self):
        if self._data_writer.get_n_vertices() == 0:
            return
        with FecTimer("SpynnakerSplitterPartitioner", TimerWork.OTHER):
            n_chips_in_graph = spynnaker_splitter_partitioner()
            self._data_writer.set_n_chips_in_graph(n_chips_in_graph)

# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from lazyarray import __version__ as lazyarray_version
from quantities import __version__ as quantities_version
import math
from neo import __version__ as neo_version
import os
from pyNN.common import control as pynn_control
from pyNN import __version__ as pynn_version
from typing import Collection, Optional, Union, cast
from typing_extensions import Literal

from spinn_utilities.log import FormatAdapter
from spinn_utilities.config_holder import (
    get_config_bool, get_config_str_or_none)
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.abstract_spinnaker_base import (
    AbstractSpinnakerBase)
from spinn_front_end_common.interface.provenance import (
    FecTimer, GlobalProvenance, TimerCategory, TimerWork)
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.exceptions import ConfigurationException

from spynnaker import _version
from spynnaker.pyNN import model_binaries
from spynnaker.pyNN.config_setup import CONFIG_FILE_NAME, setup_configs
from spynnaker.pyNN.models.recorder import Recorder
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter
from spynnaker.pyNN.extra_algorithms import (
    delay_support_adder, neuron_expander, synapse_expander,
    redundant_packet_count_report,
    spynnaker_neuron_graph_network_specification_report)
from spynnaker.pyNN.extra_algorithms.connection_holder_finisher import (
    finish_connection_holders)
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    spynnaker_splitter_selector)
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.neo_buffer_database import NeoBufferDatabase


logger = FormatAdapter(logging.getLogger(__name__))


class SpiNNaker(AbstractSpinnakerBase, pynn_control.BaseState):
    """
    Main interface for the sPyNNaker implementation of PyNN 0.8/0.9.
    """

    __slots__ = ("__recorders", )

    def __init__(
            self, time_scale_factor: Optional[int],
            min_delay: Union[float, None, Literal["auto"]],
            n_chips_required: Optional[int] = None,
            n_boards_required: Optional[int] = None,
            timestep: Optional[float] = 0.1):
        """
        :param time_scale_factor:
            multiplicative factor to the machine time step
            (does not affect the neuron models accuracy)
        :type time_scale_factor: int or None
        :param min_delay:
        :param n_chips_required:
            Deprecated! Use n_boards_required instead.
            Must be `None` if n_boards_required specified.
        :type n_chips_required: int or None
        :param n_boards_required:
            if you need to be allocated a machine (for spalloc) before
            building your graph, then fill this in with a general idea of
            the number of boards you need so that the spalloc system can
            allocate you a machine big enough for your needs.
        :type n_boards_required: int or None
        :param timestep:
            the time step of the simulations in microseconds;
            if `None` the cfg value is used
        :type timestep: float or None
        """
        # pylint: disable=too-many-arguments, too-many-locals

        # change min delay auto to be the min delay supported by simulator
        if min_delay == "auto":
            min_delay = timestep

        # pynn demanded objects
        self.__recorders: Collection[Recorder] = set()

        # main pynn interface inheritance
        pynn_control.BaseState.__init__(self)

        # SpiNNaker setup
        setup_configs()

        # add model binaries
        # called before super.init as that logs the paths
        SpynnakerDataView.register_binary_search_path(
            os.path.dirname(model_binaries.__file__))

        super().__init__(SpynnakerDataWriter)

        self.__writer.set_n_required(n_boards_required, n_chips_required)
        # set up machine targeted data
        self._set_up_timings(timestep, min_delay, time_scale_factor)

        with GlobalProvenance() as db:
            db.insert_version("sPyNNaker_version", _version.__version__)
            db.insert_version("pyNN_version", pynn_version)
            db.insert_version("quantities_version", quantities_version)
            db.insert_version("neo_version", neo_version)
            db.insert_version("lazyarray_version", lazyarray_version)

    @property
    def __writer(self) -> SpynnakerDataWriter:
        return cast(SpynnakerDataWriter, self._data_writer)

    def _clear_and_run(self, run_time: Optional[float],
                       sync_time: float = 0.0):
        """
        Clears the projections and Run the model created.

        :param run_time: the time (in milliseconds) to run the simulation for
        :type run_time: float or int or None
        :param float sync_time:
            If not 0, this specifies that the simulation should pause after
            this duration.  The continue_simulation() method must then be
            called for the simulation to continue.
        """
        # sPyNNaker specific algorithms to do before starting a run
        self.__flush_post_vertex_caches()

        super(SpiNNaker, self).run(run_time, sync_time)

        # PyNNaker specific algorithms to do after finishing a run
        self.__flush_post_vertex_caches()

    def __flush_post_vertex_caches(self) -> None:
        # pylint: disable=protected-access
        for projection in self.__writer.iterate_projections():
            projection._clear_cache()

    def run(self, run_time: Optional[float], sync_time: float = 0.0):
        """
        Run the simulation for a span of simulation time.

        :param run_time: the time to run for, in milliseconds
        """
        self._clear_and_run(run_time, sync_time)

    def run_until(self, tstop: float):
        """
        Run the simulation until the given simulation time.

        :param tstop: when to run until in milliseconds
        """
        # Build data
        self._clear_and_run(tstop - self.t)

    def clear(self) -> None:
        """
        Clear the current recordings and reset the simulation.
        """
        self.recorders = set()
        self.reset()

        # Stop any currently running SpiNNaker application
        self.stop()

    def reset(self) -> None:
        """
        Reset the state of the current network to time t = 0.
        """
        if not self.__writer.is_ran_last():
            if not self.__writer.is_ran_ever():
                logger.error("Ignoring the reset before the run")
            else:
                logger.error("Ignoring the repeated reset call")
            return
        for population in self.__writer.iterate_populations():
            population._cache_data()  # pylint: disable=protected-access

        # Call superclass implementation
        AbstractSpinnakerBase.reset(self)

    @property
    def state(self) -> 'SpiNNaker':
        """
        Used to bypass the dual level object.

        :return: the SpiNNaker object
        :rtype: ~spynnaker.pyNN.SpiNNaker
        """
        return self

    @property
    def mpi_rank(self) -> int:
        """
        The MPI rank of the simulator.

        .. note::
            Meaningless on SpiNNaker, so we pretend we're the head node.

        :return: Constant: 0
        :rtype: int
        """
        return 0

    @mpi_rank.setter
    def mpi_rank(self, new_value):
        """
         sPyNNaker does not use this value meaningfully.

        :param new_value: Ignored
        """

    @property
    def num_processes(self) -> int:
        """
        The number of MPI worker processes.

        .. note::
            Meaningless on SpiNNaker, so we pretend there's one MPI process

        :return: Constant: 1
        :rtype: int
        """
        return 1

    @num_processes.setter
    def num_processes(self, new_value):
        """
        sPyNNaker does not use this value meaningfully.

        :param new_value: Ignored
        """

    @property
    def dt(self) -> float:
        """
        The simulation time step in milliseconds.

        :return: the machine time step
        :rtype: float
        """
        return self.__writer.get_simulation_time_step_ms()

    @dt.setter
    def dt(self, _):
        """
        We do not support setting the time step except during setup.

        :raises NotImplementedError
        """
        raise NotImplementedError(
            "We do not support setting dt/ time step except during setup")

    @property
    def t(self) -> float:
        """
        The current simulation time in milliseconds.

        :return: the current runtime already executed
        :rtype: float
        """
        return self.__writer.get_current_run_time_ms()

    @property
    def segment_counter(self) -> int:
        """
        The number of the current recording segment being generated.

        :return: the segment counter
        :rtype: int
        """
        return self.__writer.get_segment_counter()

    @segment_counter.setter
    def segment_counter(self, _):
        """
        We do not support externally altering the segment counter

        raises: NotImplementedError
        """
        raise NotImplementedError(
            "We do not support externally altering the segment counter")

    @property
    def name(self) -> str:
        """
        The name of the simulator. Used to ensure PyNN recording neo
        blocks are correctly labelled.

        :return: the name of the simulator.
        :rtype: str
        """
        return _version._NAME  # pylint: disable=protected-access

    @property
    def recorders(self) -> Collection[Recorder]:
        """
        The recorders, used by the PyNN state object.

        :return: the internal recorders object
        :rtype: list(~spynnaker.pyNN.models.recorder.Recorder)
        """
        return self.__recorders

    @recorders.setter
    def recorders(self, new_value: Collection[Recorder]):
        """
        Setter for the internal recorders object

        :param new_value: the new value for the recorder
        """
        self.__recorders = set(new_value)

    def _set_up_timings(
            self, timestep: Optional[float], min_delay: Union[
                int, float, None],
            time_scale_factor: Optional[int]):
        """
        :param timestep: machine_time_Step in milliseconds
        :type timestep: float or None
        :param min_delay:
        :type min_delay: int or float or None
        :param time_scale_factor:
        :type time_scale_factor: int or None
        """
        # Get the standard values
        if timestep is None:
            self.__writer.set_up_timings_and_delay(
                timestep, time_scale_factor, min_delay)
        else:
            self.__writer.set_up_timings_and_delay(
                math.ceil(timestep * MICRO_TO_MILLISECOND_CONVERSION),
                time_scale_factor, min_delay)

        # Check the combination of machine time step and time scale factor
        if (self.__writer.get_simulation_time_step_ms() *
                self.__writer.get_time_scale_factor() < 1):
            if not get_config_bool(
                    "Mode", "violate_1ms_wall_clock_restriction"):
                raise ConfigurationException(
                    "The combination of simulation time step and the machine "
                    "time scale factor results in a wall clock timer tick "
                    "that is currently not reliably supported by the"
                    "SpiNNaker machine.  If you would like to override this"
                    "behaviour (at your own risk), please add "
                    "violate_1ms_wall_clock_restriction = True to the [Mode] "
                    f"section of your .{CONFIG_FILE_NAME} file")
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

    def stop(self) -> None:
        """
        End running of the simulation. Notifying each Population of the end.
        """
        # pylint: disable=protected-access
        FecTimer.start_category(TimerCategory.SHUTTING_DOWN)
        for population in self.__writer.iterate_populations():
            population._end()

        super().stop()

    @staticmethod
    def register_binary_search_path(search_path: str):
        """
        Register an additional binary search path for executables.

        .. deprecated:: 7.0
            Use :py:meth:`SpynnakerDataView.register_binary_search_path`.

        :param str search_path: absolute search path for binaries
        """
        # pylint: disable=protected-access
        SpynnakerDataView.register_binary_search_path(search_path)

    def _execute_write_neo_metadata(self) -> None:
        with FecTimer("Write Neo Metadata", TimerWork.OTHER):
            with NeoBufferDatabase() as db:
                db.write_segment_metadata()
                db.write_metadata()

    @overrides(AbstractSpinnakerBase._do_write_metadata)
    def _do_write_metadata(self) -> None:
        self._execute_write_neo_metadata()
        super()._do_write_metadata()

    def _execute_synapse_expander(self) -> None:
        with FecTimer("Synapse expander", TimerWork.SYNAPSE) as timer:
            if timer.skip_if_virtual_board():
                return
            synapse_expander()

    def _execute_neuron_expander(self) -> None:
        with FecTimer("Neuron expander", TimerWork.SYNAPSE) as timer:
            if timer.skip_if_virtual_board():
                return
            neuron_expander()

    def _execute_finish_connection_holders(self) -> None:
        with FecTimer("Finish connection holders", TimerWork.OTHER):
            finish_connection_holders()

    @overrides(AbstractSpinnakerBase._do_extra_load_algorithms)
    def _do_extra_load_algorithms(self) -> None:
        self._execute_neuron_expander()
        self._execute_synapse_expander()
        self._execute_finish_connection_holders()

    def _report_write_network_graph(self) -> None:
        with FecTimer("SpYNNakerNeuronGraphNetworkSpecificationReport",
                      TimerWork.REPORT) as timer:
            if timer.skip_if_cfg_false("Reports", "write_network_graph"):
                return
            spynnaker_neuron_graph_network_specification_report()

    @overrides(AbstractSpinnakerBase._do_extra_mapping_algorithms,
               extend_doc=False)
    def _do_extra_mapping_algorithms(self) -> None:
        self._report_write_network_graph()

    @overrides(AbstractSpinnakerBase._do_provenance_reports)
    def _do_provenance_reports(self) -> None:
        AbstractSpinnakerBase._do_provenance_reports(self)
        self._report_redundant_packet_count()

    def _report_redundant_packet_count(self) -> None:
        with FecTimer("Redundant packet count report",
                      TimerWork.REPORT) as timer:
            if timer.skip_if_cfg_false(
                    "Reports", "write_redundant_packet_count_report"):
                return
            redundant_packet_count_report()

    @overrides(AbstractSpinnakerBase._execute_splitter_selector)
    def _execute_splitter_selector(self) -> None:
        with FecTimer("Spynnaker splitter selector", TimerWork.OTHER):
            spynnaker_splitter_selector()

    @overrides(AbstractSpinnakerBase._execute_delay_support_adder,
               extend_doc=False)
    def _execute_delay_support_adder(self) -> None:
        """
        Runs, times and logs the DelaySupportAdder if required.
        """
        name = get_config_str_or_none("Mapping", "delay_support_adder")
        if name is None:
            return
        with FecTimer("DelaySupportAdder", TimerWork.OTHER):
            if name == "DelaySupportAdder":
                d_vertices, d_edges = delay_support_adder()
                for vertex in d_vertices:
                    self.__writer.add_vertex(vertex)
                for edge in d_edges:
                    self.__writer.add_edge(edge, constants.SPIKE_PARTITION_ID)
                return
            raise ConfigurationException(
                f"Unexpected cfg setting delay_support_adder: {name}")

    @overrides(AbstractSpinnakerBase._execute_buffer_extractor)
    def _execute_buffer_extractor(self) -> None:
        super()._execute_buffer_extractor()
        if not get_config_bool("Machine", "virtual_board"):
            with NeoBufferDatabase() as db:
                db.write_t_stop()

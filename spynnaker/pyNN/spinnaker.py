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
from lazyarray import __version__ as lazyarray_version
from quantities import __version__ as quantities_version
from neo import __version__ as neo_version
from pyNN.common import control as pynn_control
from pyNN.random import RandomDistribution, NumpyRNG
from pyNN import __version__ as pynn_version
from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.failed_state import FAILED_STATE_MSG
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
from spynnaker.pyNN.utilities.spynnaker_failed_state import (
    SpynnakerFailedState)
from spynnaker.pyNN import _version
from spynnaker.pyNN.spynnaker8_simulator_interface import (
    Spynnaker8SimulatorInterface)
from spynnaker.pyNN.utilities.random_stats import (
    RandomStatsExponentialImpl, RandomStatsGammaImpl, RandomStatsLogNormalImpl,
    RandomStatsNormalClippedImpl, RandomStatsNormalImpl,
    RandomStatsPoissonImpl, RandomStatsRandIntImpl, RandomStatsUniformImpl,
    RandomStatsVonmisesImpl, RandomStatsBinomialImpl)
from ._version import __version__ as version

log = FormatAdapter(logging.getLogger(__name__))
NAME = "SpiNNaker_under_version({}-{})".format(
    _version.__version__, _version.__version_name__)


class SpiNNaker(AbstractSpiNNakerCommon, pynn_control.BaseState,
                Spynnaker8SimulatorInterface):
    """ Main interface for the sPyNNaker implementation of PyNN 0.8/0.9
    """

    def __init__(
            self, database_socket_addresses,
            extra_algorithm_xml_paths, extra_mapping_inputs,
            extra_mapping_algorithms, extra_pre_run_algorithms,
            extra_post_run_algorithms, extra_load_algorithms,
            time_scale_factor, min_delay, max_delay, graph_label,
            n_chips_required=None, n_boards_required=None, timestep=0.1,
            hostname=None):
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

        # handle the extra load algorithms and the built in ones
        built_in_extra_load_algorithms = list()
        if extra_load_algorithms is not None:
            built_in_extra_load_algorithms.extend(extra_load_algorithms)

        # handle extra xmls and the ones needed by default
        built_in_extra_xml_paths = list()
        if extra_algorithm_xml_paths is not None:
            built_in_extra_xml_paths.extend(extra_algorithm_xml_paths)

        # handle the extra mapping inputs and the built in ones
        built_in_extra_mapping_inputs = dict()
        if extra_mapping_inputs is not None:
            built_in_extra_mapping_inputs.update(extra_mapping_inputs)

        front_end_versions = [("sPyNNaker8_version", version)]
        front_end_versions.append(("pyNN_version", pynn_version))
        front_end_versions.append(("quantities_version", quantities_version))
        front_end_versions.append(("neo_version", neo_version))
        front_end_versions.append(("lazyarray_version", lazyarray_version))

        # SpiNNaker setup
        super(SpiNNaker, self).__init__(
            database_socket_addresses=database_socket_addresses,
            user_extra_algorithm_xml_path=built_in_extra_xml_paths,
            user_extra_mapping_inputs=built_in_extra_mapping_inputs,
            extra_mapping_algorithms=extra_mapping_algorithms,
            user_extra_algorithms_pre_run=extra_pre_run_algorithms,
            extra_post_run_algorithms=extra_post_run_algorithms,
            extra_load_algorithms=built_in_extra_load_algorithms,
            graph_label=graph_label, n_chips_required=n_chips_required,
            n_boards_required=n_boards_required,
            hostname=hostname, min_delay=min_delay,
            max_delay=max_delay, timestep=timestep,
            time_scale_factor=time_scale_factor,
            front_end_versions=front_end_versions)

    def run(self, run_time):
        """ Run the simulation for a span of simulation time.

        :param run_time: the time to run for, in milliseconds
        :return: None
        """

        self._run_wait(run_time)

    def run_until(self, tstop):
        """ Run the simulation until the given simulation time.

        :param tstop: when to run until in milliseconds
        """
        # Build data
        self._run_wait(tstop - self.t)

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
            population.cache_data()

        self.__segment_counter += 1

        AbstractSpiNNakerCommon.reset(self)

    def _run_wait(self, duration_ms):
        """ Run the simulation for a length of simulation time.

        :param duration_ms: The run duration, in milliseconds
        :type duration_ms: int or float
        """

        # Convert dt into microseconds and divide by
        # realtime proportion to get hardware timestep
        hardware_timestep_us = int(round(
            float(self.machine_time_step) / float(self.timescale_factor)))

        # Determine how long simulation is in timesteps
        duration_timesteps = int(math.ceil(
            float(duration_ms) / float(self.dt)))

        log.info(
            "Simulating for {} {}ms timesteps using a hardware timestep "
            "of {}us", duration_timesteps, self.dt, hardware_timestep_us)

        super(SpiNNaker, self).run(duration_ms)

    @property
    def state(self):
        """ Used to bypass the dual level object

        :return: the SpiNNaker object
        :rtype: spynnaker8.spinnaker.SpiNNaker
        """
        return self

    @property
    def mpi_rank(self):
        """ Gets the MPI rank of the simulator

        .. note::
            Meaningless on SpiNNaker, so we pretend we're the head node.

        :return: Constant: 0
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
        """
        return 1

    @num_processes.setter
    def num_processes(self, new_value):
        """ sPyNNaker does not use this value meaningfully

        :param new_value: Ignored
        """

    @property
    def dt(self):
        """ The machine time step.

        :return: the machine time step
        """

        return self.machine_time_step / float(MICRO_TO_MILLISECOND_CONVERSION)

    @dt.setter
    def dt(self, new_value):
        """ The machine time step

        :param new_value: new value for machine time step
        """
        self.machine_time_step = new_value * MICRO_TO_MILLISECOND_CONVERSION

    @property
    def t(self):
        """ The current simulation time

        :return: the current runtime already executed
        """
        return (
            self._current_run_timesteps * (self.machine_time_step / 1000.0))

    @property
    def segment_counter(self):
        """ The number of the current recording segment being generated.

        :return: the segment counter
        """
        return self.__segment_counter

    @segment_counter.setter
    def segment_counter(self, new_value):
        """ The number of the current recording segment being generated.

        :param new_value: new value for the segment counter
        """
        self.__segment_counter = new_value

    @property
    def running(self):
        """ Whether the simulation is running or has run.

        .. note::
            Ties into our has_ran parameter for automatic pause and resume.

        :return: the has_ran variable from the SpiNNaker main interface
        """
        return self._has_ran

    @running.setter
    def running(self, new_value):
        """ Setter for the has_ran parameter, only used by the PyNN interface,\
            supports tracking where it thinks its setting this parameter.

        :param new_value: the new value for the simulation
        """
        self._has_ran = new_value

    @property
    def name(self):
        """ The name of the simulator. Used to ensure PyNN recording neo\
            blocks are correctly labelled.

        :return: the name of the simulator.
        """
        return NAME

    @property
    def populations(self):
        """ The list of all populations in the simulation.

        :return: list of populations
        """
        # needed by the population class
        return self._populations

    @property
    def projections(self):
        """ The list of all projections in the simulation.

        :return: list of projections
        """
        # needed by the projection class.
        return self._projections

    @property
    def recorders(self):
        """ The recorders, used by the PyNN state object

        :return: the internal recorders object
        """
        return self.__recorders

    @recorders.setter
    def recorders(self, new_value):
        """ Setter for the internal recorders object

        :param new_value: the new value for the recorder
        """
        self.__recorders = new_value

    def get_distribution_to_stats(self):
        return {
            'binomial': RandomStatsBinomialImpl(),
            'gamma': RandomStatsGammaImpl(),
            'exponential': RandomStatsExponentialImpl(),
            'lognormal': RandomStatsLogNormalImpl(),
            'normal': RandomStatsNormalImpl(),
            'normal_clipped': RandomStatsNormalClippedImpl(),
            'normal_clipped_to_boundary': RandomStatsNormalClippedImpl(),
            'poisson': RandomStatsPoissonImpl(),
            'uniform': RandomStatsUniformImpl(),
            'randint': RandomStatsRandIntImpl(),
            'vonmises': RandomStatsVonmisesImpl()}

    def get_random_distribution(self):
        return RandomDistribution

    def is_a_pynn_random(self, thing):
        return isinstance(thing, RandomDistribution)

    def get_pynn_NumpyRNG(self):
        return NumpyRNG


# Defined in this file to prevent an import loop
class Spynnaker8FailedState(SpynnakerFailedState,
                            Spynnaker8SimulatorInterface):
    __slots__ = ("write_on_end")

    def __init__(self):
        self.write_on_end = []

    @property
    def dt(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def mpi_rank(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def name(self):
        return NAME

    @property
    def num_processes(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def recorders(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def segment_counter(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def t(self):
        raise ConfigurationException(FAILED_STATE_MSG)


# At import time change the default FailedState
globals_variables.set_failed_state(Spynnaker8FailedState())

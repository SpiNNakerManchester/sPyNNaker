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

from lazyarray import __version__ as lazyarray_version
from quantities import __version__ as quantities_version
from neo import __version__ as neo_version
from pyNN.common import control as pynn_control
from pyNN import __version__ as pynn_version
from spinn_front_end_common.interface.abstract_spinnaker_base import (
    AbstractSpinnakerBase)
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
from spynnaker import _version


class SpiNNaker(AbstractSpiNNakerCommon, pynn_control.BaseState):
    """ Main interface for the sPyNNaker implementation of PyNN 0.8/0.9
    """

    def __init__(
            self, database_socket_addresses,
            time_scale_factor, min_delay, graph_label,
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

        # SpiNNaker setup
        super(SpiNNaker, self).__init__(
            database_socket_addresses=database_socket_addresses,
            graph_label=graph_label, n_chips_required=n_chips_required,
            n_boards_required=n_boards_required,
            hostname=hostname, min_delay=min_delay,
            timestep=timestep, time_scale_factor=time_scale_factor)

        with ProvenanceWriter() as db:
            db.insert_version("sPyNNaker_version", _version.__version__)
            db.insert_version("pyNN_version", pynn_version)
            db.insert_version("quantities_version", quantities_version)
            db.insert_version("neo_version", neo_version)
            db.insert_version("lazyarray_version", lazyarray_version)

    def run(self, run_time, sync_time=0.0):
        """ Run the simulation for a span of simulation time.

        :param run_time: the time to run for, in milliseconds
        :return: None
        """

        self._run_wait(run_time, sync_time)

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
            population._cache_data()

        self.__segment_counter += 1

        # Call superclass implementation
        AbstractSpinnakerBase.reset(self)

    def _run_wait(self, duration_ms, sync_time=0.0):
        """ Run the simulation for a length of simulation time.

        :param duration_ms: The run duration, in milliseconds
        :type duration_ms: int or float
        """

        super(SpiNNaker, self).run(duration_ms, sync_time)

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
        """ The simulation time step in milliseconds

        :return: the machine time step
        :rtype: float
        """
        return self._data_writer.get_simulation_time_step_ms()

    @dt.setter
    def dt(self, new_value):
        """ We do not support setting dt/ time step except during setup

        :param float new_value: new value for machine time step in microseconds
        """
        raise NotImplementedError(
            "We do not support setting dt/ time step except during setup")

    @property
    def t(self):
        """ The current simulation time in milliseconds

        :return: the current runtime already executed
        :rtype: float
        """
        return (self._data_writer.get_current_run_time_ms())

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
        return _version._NAME

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

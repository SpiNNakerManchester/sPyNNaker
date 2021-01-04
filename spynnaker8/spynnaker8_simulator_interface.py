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

from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty)
from spynnaker.pyNN.spynnaker_simulator_interface import (
    SpynnakerSimulatorInterface)


@add_metaclass(AbstractBase)
class Spynnaker8SimulatorInterface(SpynnakerSimulatorInterface):
    """ The API exposed by the simulator itself.
    """

    __slots__ = ()

    @abstractproperty
    def dt(self):
        """ The timestep, in milliseconds. """

    @abstractproperty
    def mpi_rank(self):
        """ The MPI rank of the controller node. """

    @abstractproperty
    def name(self):
        """ The name of the simulator. Used to ensure PyNN recording neo\
            blocks are correctly labelled. """

    @abstractproperty
    def num_processes(self):
        """ The number of MPI worker processes. """

    @abstractproperty
    def recorders(self):
        """ The recorders, used by the PyNN state object. """

    @abstractproperty
    def segment_counter(self):
        """ The number of the current recording segment being generated. """

    @abstractproperty
    def t(self):
        """ The current simulation time, in milliseconds. """

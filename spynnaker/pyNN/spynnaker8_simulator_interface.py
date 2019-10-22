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

    __slots__ = ()

    @abstractproperty
    def dt(self):
        pass

    @abstractproperty
    def mpi_rank(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def num_processes(self):
        pass

    @abstractproperty
    def recorders(self):
        pass

    @abstractproperty
    def segment_counter(self):
        pass

    @abstractproperty
    def t(self):
        pass

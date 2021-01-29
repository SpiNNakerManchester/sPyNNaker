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

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from .rate_source_array_partition import RateSourceArrayPartition

DEFAULT_MAX_ATOMS_PER_CORE = 500

class RateSourceArray(AbstractPyNNModel):

    default_population_parameters = {}

    def __init__(self, rate_times=[], rate_values=[], looping=0, partitions=1):

        if len(rate_times) != len(rate_values):
            raise Exception("Rate Source Array Error: Rate times and Rate Values must have the same length.")
        self.__rate_times = rate_times
        self.__rate_values = rate_values
        self.__looping = looping
        self.__partitions = partitions

    @overrides(AbstractPyNNModel.create_vertex)
    def create_vertex(
            self, n_neurons, label, constraints):
        max_atoms = self.get_max_atoms_per_core()
        return RateSourceArrayPartition(
            n_neurons, self.__rate_times, self.__rate_values,
            constraints, label, max_atoms, self, self.__looping, self.__partitions)

    @property
    def _rate_times(self):
        return self.__spike_times

    @property
    def _rate_values(self):
        return self.__rate_values

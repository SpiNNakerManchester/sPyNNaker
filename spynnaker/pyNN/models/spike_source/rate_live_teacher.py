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
from .rate_live_teacher_partition import RateLiveTeacherPartition

class RateLiveTeacher(AbstractPyNNModel):

    default_population_parameters = {}

    def __init__(self, sources, refresh_rate, dataset, partitions=1):

        self.__sources = sources
        self.__partitions = partitions
        # Number of classes for MNIST. To Be Changed!
        self._max_atoms_per_core = 10
        # Numer of timesteps we want to keep each rate fixed
        self.__refresh_rate = refresh_rate
        self.__dataset = dataset

    @overrides(AbstractPyNNModel.create_vertex)
    def create_vertex(
            self, n_neurons, label, constraints):
        return RateLiveTeacherPartition(
            self.__sources, constraints, label,
            self, self.__partitions,
            self.__refresh_rate, self.__dataset)

    @property
    def _sources(self):
        return self.__sources
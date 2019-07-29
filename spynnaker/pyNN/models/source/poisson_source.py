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

from .poisson_source_vertex import PoissonSourceVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spinn_utilities.overrides import overrides

_population_parameters = {"seed": None,  "max_rate": None}

# Technically, this is ~2900 in terms of DTCM, but is timescale dependent
# in terms of CPU (2900 at 10 times slow down is fine, but not at
# real-time)
DEFAULT_MAX_ATOMS_PER_CORE = 500


class PoissonSource(AbstractPyNNModel):
    __slots__ = ["__duration", "__rate", "__start", "__poisson_weight"]

    default_population_parameters = _population_parameters

    def __init__(self, rate=1.0, start=0, duration=None, poisson_weight=1.0):
        self.__start = start
        self.__duration = duration
        self.__rate = rate
        self.__poisson_weight = poisson_weight

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_CORE):
        super(PoissonSource, cls).set_model_max_atoms_per_core(
            n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super(PoissonSource, cls)._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_CORE
        return super(PoissonSource, cls).get_max_atoms_per_core()

    @overrides(AbstractPyNNModel.create_vertex, additional_arguments=[
        "seed", "max_rate"])
    def create_vertex(self, n_neurons, label, constraints, seed, max_rate):
        max_atoms = self.get_max_atoms_per_core()
        return PoissonSourceVertex(
            n_neurons, constraints, label, self.__rate, max_rate, self.__start,
            self.__duration, seed, max_atoms, self, self.__poisson_weight)

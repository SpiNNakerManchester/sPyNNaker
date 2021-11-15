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

from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spinn_utilities.overrides import overrides

_population_parameters = {
    "seed": None,  "max_rate": 1000, "splitter": None}

# Technically, this is ~2900 in terms of DTCM, but is timescale dependent
# in terms of CPU (2900 at 10 times slow down is fine, but not at
# real-time)
DEFAULT_MAX_ATOMS_PER_CORE = 500


class SpikeSourcePoisson(AbstractPyNNModel):
    __slots__ = ["__duration", "__rate", "__start"]

    default_population_parameters = _population_parameters

    def __init__(self, rate=1.0, start=0, duration=None):
        self.__start = start
        self.__duration = duration
        self.__rate = rate

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_CORE):
        super().set_model_max_atoms_per_core(n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super()._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_CORE
        return super().get_max_atoms_per_core()

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=default_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, seed, max_rate, splitter):
        # pylint: disable=arguments-differ
        max_atoms = self.get_max_atoms_per_core()
        return SpikeSourcePoissonVertex(
            n_neurons, constraints, label, seed, max_atoms, self,
            rate=self.__rate, start=self.__start, duration=self.__duration,
            max_rate=max_rate, splitter=splitter)

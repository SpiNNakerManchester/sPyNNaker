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
from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

_population_parameters = {"seed": None, "splitter": None}

DEFAULT_MAX_ATOMS_PER_CORE = 500


class SpikeSourcePoissonVariable(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    def __init__(self, rates, starts, durations=None):
        self._rates = rates
        self._starts = starts
        self._durations = durations

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
            self, n_neurons, label, constraints, seed, splitter):
        # pylint: disable=arguments-differ
        max_atoms = self.get_max_atoms_per_core()
        return SpikeSourcePoissonVertex(
            n_neurons, constraints, label, seed, max_atoms, self,
            rates=self._rates, starts=self._starts, durations=self._durations,
            splitter=splitter)

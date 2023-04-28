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
from spinn_utilities.overrides import overrides
from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spinn_utilities.classproperty import classproperty

_population_parameters = {"seed": None, "splitter": None}

DEFAULT_MAX_ATOMS_PER_CORE = 500


class SpikeSourcePoissonVariable(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    def __init__(self, rates, starts, durations=None):
        self._rates = rates
        self._starts = starts
        self._durations = durations

    @classproperty
    def absolute_max_atoms_per_core(cls):  # pylint: disable=no-self-argument
        return DEFAULT_MAX_ATOMS_PER_CORE

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=default_population_parameters.keys())
    def create_vertex(self, n_neurons, label, seed, splitter):
        """
        :param float seed:
        :param splitter:
        :type splitter:
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon or None
        """
        # pylint: disable=arguments-differ
        max_atoms = self.get_model_max_atoms_per_dimension_per_core()
        return SpikeSourcePoissonVertex(
            n_neurons, label, seed, max_atoms, self, rates=self._rates,
            starts=self._starts, durations=self._durations, splitter=splitter)

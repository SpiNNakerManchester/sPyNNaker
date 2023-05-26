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

from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spinn_utilities.overrides import overrides
from spinn_utilities.classproperty import classproperty

_population_parameters = {
    "seed": None, "max_rate": None, "splitter": None,
    "n_colour_bits": None}

# Technically, this is ~2900 in terms of DTCM, but is timescale dependent
# in terms of CPU (2900 at 10 times slow down is fine, but not at
# real-time)
DEFAULT_MAX_ATOMS_PER_CORE = 500


class SpikeSourcePoisson(AbstractPyNNModel):
    """
    A model of a Poisson-distributed source of spikes.
    """
    __slots__ = ("__duration", "__rate", "__start")

    default_population_parameters = _population_parameters

    def __init__(self, rate=1.0, start=0, duration=None):
        self.__start = start
        self.__duration = duration
        self.__rate = rate

    @classproperty
    def absolute_max_atoms_per_core(cls):  # pylint: disable=no-self-argument
        return DEFAULT_MAX_ATOMS_PER_CORE

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=default_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, seed, max_rate, splitter, n_colour_bits):
        """
        :param float seed:
        :param float max_rate:
        :param splitter:
        :type splitter:
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon or None
        :param int n_colour_bits:
        """
        # pylint: disable=arguments-differ
        max_atoms = self.get_model_max_atoms_per_dimension_per_core()
        return SpikeSourcePoissonVertex(
            n_neurons, label, seed, max_atoms, self,
            rate=self.__rate, start=self.__start, duration=self.__duration,
            max_rate=max_rate, splitter=splitter, n_colour_bits=n_colour_bits)

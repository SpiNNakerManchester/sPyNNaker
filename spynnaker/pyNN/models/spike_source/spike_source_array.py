# Copyright (c) 2014 The University of Manchester
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

from typing import Optional, Union, Tuple
from spinn_utilities.overrides import overrides
from pacman.model.partitioner_splitters import AbstractSplitterCommon
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.common.types import Spikes
from .spike_source_array_vertex import SpikeSourceArrayVertex


class SpikeSourceArray(AbstractPyNNModel):
    """
    Model that creates a Spike Source Array Vertex
    """
    default_population_parameters = {
        "splitter": None, "n_colour_bits": None, "neurons_per_core": None}

    def __init__(self, spike_times: Optional[Spikes] = None):
        """
        :param spike_times: Timesteps on which to spike
        """
        if spike_times is None:
            spike_times = []
        self.__spike_times = spike_times

    @overrides(AbstractPyNNModel.create_vertex)
    def create_vertex(
            self, n_neurons: int, label: str, *,
            splitter: Optional[AbstractSplitterCommon] = None,
            neurons_per_core: Optional[Union[int, Tuple[int, ...]]] = None,
            n_colour_bits: Optional[int] = None) -> SpikeSourceArrayVertex:
        """
        :param splitter:
        :param n_colour_bits:
        """
        if neurons_per_core is None:
            neurons_per_core = \
                self.get_model_max_atoms_per_dimension_per_core()
        return SpikeSourceArrayVertex(
            n_neurons, self.__spike_times, label, neurons_per_core, self,
            splitter, n_colour_bits)

    @property
    def _spike_times(self) -> Spikes:
        return self.__spike_times

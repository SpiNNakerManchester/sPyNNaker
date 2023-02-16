# Copyright (c) 2014 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from .spike_source_array_vertex import SpikeSourceArrayVertex


class SpikeSourceArray(AbstractPyNNModel):

    default_population_parameters = {
        "splitter": None, "n_colour_bits": None}

    def __init__(self, spike_times=None):
        if spike_times is None:
            spike_times = []
        self.__spike_times = spike_times

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=default_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, splitter, n_colour_bits):
        # pylint: disable=arguments-differ
        max_atoms = self.get_model_max_atoms_per_dimension_per_core()
        return SpikeSourceArrayVertex(
            n_neurons, self.__spike_times, label, max_atoms, self, splitter,
            n_colour_bits)

    @property
    def _spike_times(self):
        return self.__spike_times

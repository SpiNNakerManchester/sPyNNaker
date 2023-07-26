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
from typing import Any, Dict, Optional
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH
from spynnaker.pyNN.models.neuron.implementations import AbstractNeuronImpl
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    SplitterAbstractPopulationVertex)

# The maximum atoms per core is the master population table row length to
# make it easier when all-to-all-connector is used
DEFAULT_MAX_ATOMS_PER_CORE = POP_TABLE_MAX_ROW_LENGTH

_population_parameters: Dict[str, Any] = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "incoming_spike_buffer_size": None, "drop_late_spikes": None,
    "splitter": None, "seed": None, "n_colour_bits": None
}


class AbstractPyNNNeuronModel(AbstractPyNNModel):
    __slots__ = ("__model", )

    #: Population parameters for neuron models.
    default_population_parameters = _population_parameters

    def __init__(self, model: AbstractNeuronImpl):
        """
        :param AbstractNeuronImpl model: The model implementation
        """
        self.__model = model

    @property
    def _model(self) -> AbstractNeuronImpl:
        return self.__model

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons: int, label: str, *,
            spikes_per_second: Optional[float] = None,
            ring_buffer_sigma: Optional[float] = None,
            incoming_spike_buffer_size: Optional[int] = None,
            drop_late_spikes: Optional[bool] = None,
            splitter: Optional[SplitterAbstractPopulationVertex] = None,
            seed: Optional[int] = None,
            n_colour_bits: Optional[int] = None) -> AbstractPopulationVertex:
        """
        :param float spikes_per_second:
        :param float ring_buffer_sigma:
        :param int incoming_spike_buffer_size:
        :param bool drop_late_spikes:
        :param splitter:
        :type splitter: SplitterAbstractPopulationVertex or None
        :param int seed:
        :param int n_colour_bits:
        """
        # pylint: disable=arguments-differ
        max_atoms = self.get_model_max_atoms_per_dimension_per_core()
        return AbstractPopulationVertex(
            n_neurons, label, max_atoms, spikes_per_second, ring_buffer_sigma,
            incoming_spike_buffer_size, self.__model, self,
            drop_late_spikes or False, splitter, seed, n_colour_bits)

    @property
    @overrides(AbstractPyNNModel.name)
    def name(self) -> str:
        return self.__model.model_name

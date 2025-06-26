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
from __future__ import annotations
from typing import Any, Dict, List, Optional, cast, TYPE_CHECKING, Union, Tuple

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.implementations import NeuronImplStandard
from spynnaker.pyNN.models.neuron.abstract_pynn_neuron_model import (
    AbstractPyNNNeuronModel, _population_parameters as APNM_default_params)

if TYPE_CHECKING:
    from spynnaker.pyNN.models.neuron.additional_inputs import (
        AbstractAdditionalInput)
    from spynnaker.pyNN.models.neuron.input_types import AbstractInputType
    from spynnaker.pyNN.models.neuron.neuron_models import NeuronModel
    from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
    from spynnaker.pyNN.models.neuron.threshold_types import (
        AbstractThresholdType)
    from spynnaker.pyNN.extra_algorithms.splitter_components import (
        SplitterPopulationVertex)
    from .population_vertex import PopulationVertex

_population_parameters: Dict[str, Any] = dict(APNM_default_params)
_population_parameters["n_steps_per_timestep"] = 1


class AbstractPyNNNeuronModelStandard(AbstractPyNNNeuronModel):
    """
    A neuron model that follows the sPyNNaker standard composed model
    pattern for point neurons.
    """

    __slots__ = ()

    default_population_parameters = _population_parameters

    def __init__(
            self, model_name: str, binary: str, neuron_model: NeuronModel,
            input_type: AbstractInputType, synapse_type: AbstractSynapseType,
            threshold_type: AbstractThresholdType,
            additional_input_type: Optional[AbstractAdditionalInput] = None):
        """
        :param model_name: Name of the model.
        :param binary: Name of the implementation executable.
        :param neuron_model: The model of the neuron body
        :param input_type: The model of synaptic input types
        :param synapse_type: The model of the synapses' dynamics
        :param threshold_type: The model of the firing threshold
        :param additional_input_type:
            The model (if any) of additional environmental inputs
        """
        super().__init__(NeuronImplStandard(
            model_name, binary, neuron_model, input_type, synapse_type,
            threshold_type, additional_input_type))

    @overrides(AbstractPyNNNeuronModel.create_vertex)  # type: ignore[has-type]
    def create_vertex(
            self, n_neurons: int, label: str, *,
            spikes_per_second: Optional[float] = None,
            ring_buffer_sigma: Optional[float] = None,
            max_expected_summed_weight: Optional[List[float]] = None,
            incoming_spike_buffer_size: Optional[int] = None,
            drop_late_spikes: Optional[bool] = None,
            splitter: Optional[SplitterPopulationVertex] = None,
            seed: Optional[int] = None, n_colour_bits: Optional[int] = None,
            n_steps_per_timestep: int = 1,
            neurons_per_core: Optional[Union[int, Tuple[int, ...]]] = None,
            n_synapse_cores: Optional[int] = None,
            allow_delay_extensions: Optional[bool] = None) -> PopulationVertex:
        """
        :param n_steps_per_timestep:
        """
        cast(NeuronImplStandard,
             self._model).n_steps_per_timestep = n_steps_per_timestep
        return super().create_vertex(
            n_neurons=n_neurons, label=label,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            max_expected_summed_weight=max_expected_summed_weight,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            drop_late_spikes=drop_late_spikes,
            splitter=splitter, seed=seed, n_colour_bits=n_colour_bits,
            neurons_per_core=neurons_per_core, n_synapse_cores=n_synapse_cores,
            allow_delay_extensions=allow_delay_extensions)

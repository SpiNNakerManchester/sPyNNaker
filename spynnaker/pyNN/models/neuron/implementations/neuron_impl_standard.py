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
from typing import Any, Mapping, Optional, Sequence

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.range_dictionary import RangeDictionary

from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.models.neuron.additional_inputs import (
    AbstractAdditionalInput)
from spynnaker.pyNN.models.neuron.input_types import (
    AbstractInputType, InputTypeConductance)
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModel
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType
from spynnaker.pyNN.utilities.struct import Struct, StructRepeat

from .abstract_neuron_impl import AbstractNeuronImpl

# The size of the n_steps_per_timestep parameter
_N_STEPS_PER_TIMESTEP_SIZE = 1 * BYTES_PER_WORD

# The default number of steps per timestep
_DEFAULT_N_STEPS_PER_TIMESTEP = 1

_STEPS_PER_TIMESTEP = "n_steps_per_timestep"
_STEPS_PER_TIMESTEP_STRUCT = Struct(
    [(DataType.UINT32, _STEPS_PER_TIMESTEP)], repeat_type=StructRepeat.GLOBAL)


class NeuronImplStandard(AbstractNeuronImpl):
    """
    The standard componentised neuron implementation.
    """

    __slots__ = (
        "__model_name",
        "__binary",
        "__neuron_model",
        "__input_type",
        "__synapse_type",
        "__threshold_type",
        "__additional_input_type",
        "__components",
        "__n_steps_per_timestep")

    _RECORDABLES = ["v", "gsyn_exc", "gsyn_inh"]

    _RECORDABLE_DATA_TYPES = {
        "v": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    _RECORDABLE_UNITS = {
        'v': 'mV',
        'gsyn_exc': "uS",
        'gsyn_inh': "uS"}

    def __init__(
            self, model_name: str, binary: str,
            neuron_model: NeuronModel, input_type: AbstractInputType,
            synapse_type: AbstractSynapseType,
            threshold_type: AbstractThresholdType,
            additional_input_type: Optional[AbstractAdditionalInput] = None):
        """
        :param model_name:
        :param binary:
        :param neuron_model:
        :param input_type:
        :param synapse_type:
        :param threshold_type:
        :param additional_input_type:
        """
        self.__model_name = model_name
        self.__binary = binary
        self.__neuron_model = neuron_model
        self.__input_type = input_type
        self.__synapse_type = synapse_type
        self.__threshold_type = threshold_type
        self.__additional_input_type = additional_input_type
        self.__n_steps_per_timestep = _DEFAULT_N_STEPS_PER_TIMESTEP

        self.__components = [
            self.__neuron_model, self.__input_type, self.__threshold_type,
            self.__synapse_type]
        if self.__additional_input_type is not None:
            self.__components.append(self.__additional_input_type)

    @property
    def n_steps_per_timestep(self) -> int:
        """
        Get the last set n steps per timestep
        """
        return self.__n_steps_per_timestep

    @n_steps_per_timestep.setter
    def n_steps_per_timestep(self, n_steps_per_timestep: int) -> None:
        self.__n_steps_per_timestep = n_steps_per_timestep

    @property
    @overrides(AbstractNeuronImpl.model_name)
    def model_name(self) -> str:
        return self.__model_name

    @property
    @overrides(AbstractNeuronImpl.binary_name)
    def binary_name(self) -> str:
        return self.__binary

    @property
    @overrides(AbstractNeuronImpl.structs)
    def structs(self) -> Sequence[Struct]:
        structs = [_STEPS_PER_TIMESTEP_STRUCT]
        structs.extend(s for c in self.__components for s in c.structs)
        return structs

    @overrides(AbstractNeuronImpl.get_global_weight_scale)
    def get_global_weight_scale(self) -> float:
        return self.__input_type.get_global_weight_scale()

    @overrides(AbstractNeuronImpl.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        return self.__synapse_type.get_n_synapse_types()

    @overrides(AbstractNeuronImpl.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        return self.__synapse_type.get_synapse_id_by_target(target)

    @overrides(AbstractNeuronImpl.get_synapse_targets)
    def get_synapse_targets(self) -> Sequence[str]:
        return self.__synapse_type.get_synapse_targets()

    @overrides(AbstractNeuronImpl.get_recordable_variables)
    def get_recordable_variables(self) -> Sequence[str]:
        return self._RECORDABLES

    @overrides(AbstractNeuronImpl.get_recordable_units)
    def get_recordable_units(self, variable: str) -> str:
        return self._RECORDABLE_UNITS[variable]

    @overrides(AbstractNeuronImpl.get_recordable_data_types)
    def get_recordable_data_types(self) -> Mapping[str, DataType]:
        return self._RECORDABLE_DATA_TYPES

    @overrides(AbstractNeuronImpl.is_recordable)
    def is_recordable(self, variable: str) -> bool:
        return variable in self._RECORDABLES

    @overrides(AbstractNeuronImpl.get_recordable_variable_index)
    def get_recordable_variable_index(self, variable: str) -> int:
        return self._RECORDABLES.index(variable)

    @overrides(AbstractNeuronImpl.add_parameters)
    def add_parameters(self, parameters: RangeDictionary) -> None:
        parameters[_STEPS_PER_TIMESTEP] = self.__n_steps_per_timestep
        for component in self.__components:
            component.add_parameters(parameters)

    @overrides(AbstractNeuronImpl.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary) -> None:
        for component in self.__components:
            component.add_state_variables(state_variables)

    @overrides(AbstractNeuronImpl.get_units)
    def get_units(self, variable: str) -> str:
        for component in self.__components:
            if component.has_variable(variable):
                return component.get_units(variable)

        raise KeyError(
            f"The parameter {variable} does not exist in this neuron model")

    @property
    @overrides(AbstractNeuronImpl.is_conductance_based)
    def is_conductance_based(self) -> bool:
        return isinstance(self.__input_type, InputTypeConductance)

    def __getitem__(self, key: str) -> Any:
        # Find the property in the components...
        for component in self.__components:
            if hasattr(component, key):
                return getattr(component, key)
        # ... or fail
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute {key}")

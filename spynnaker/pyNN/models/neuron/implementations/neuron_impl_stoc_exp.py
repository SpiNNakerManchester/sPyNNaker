# Copyright (c) 2023 The University of Manchester
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

from typing import Optional, Sequence, Mapping
from spinn_front_end_common.interface.ds import DataType
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractNeuronImpl, ModelParameter)
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from pyNN.random import NumpyRNG
from spynnaker.pyNN.random_distribution import RandomDistribution

TAU = "tau"
TIMESTEP = "timestep"
BIAS = "bias"
REFRACT_INIT = "refract_init"
SEED0 = "seed0"
SEED1 = "seed1"
SEED2 = "seed2"
SEED3 = "seed3"

UNITS = {
    TAU: "ms",
    BIAS: "mV",
    REFRACT_INIT: "ms",
}

MAX_INT = float(0xFFFFFFFF)


class NeuronImplStocExp(AbstractNeuronImpl):

    def __init__(self, tau: ModelParameter, bias: ModelParameter,
                 refract_init: ModelParameter, seed: int):

        self._tau = tau
        self._bias = bias
        self._refract_init = refract_init
        self._random = RandomDistribution(
            "uniform", low=0, high=0xFFFFFFFF, rng=NumpyRNG(seed))

        self._struct = Struct([
            (DataType.U1616, TAU),
            (DataType.U1616, TIMESTEP),
            (DataType.S1615, BIAS),
            (DataType.UINT32, REFRACT_INIT),
            (DataType.UINT32, SEED0),
            (DataType.UINT32, SEED1),
            (DataType.UINT32, SEED2),
            (DataType.UINT32, SEED3)])

    @property
    @overrides(AbstractNeuronImpl.structs)
    def structs(self) -> Sequence[Struct]:
        return [self._struct]

    @property
    @overrides(AbstractNeuronImpl.model_name)
    def model_name(self) -> str:
        return "StocExp"

    @property
    @overrides(AbstractNeuronImpl.binary_name)
    def binary_name(self) -> str:
        return "stoc_exp.aplx"

    @overrides(AbstractNeuronImpl.get_global_weight_scale)
    def get_global_weight_scale(self) -> float:
        return 1.0

    @overrides(AbstractNeuronImpl.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        return 2

    @overrides(AbstractNeuronImpl.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        raise ValueError("Unknown target {}".format(target))

    @overrides(AbstractNeuronImpl.get_synapse_targets)
    def get_synapse_targets(self) -> Sequence[str]:
        return ["excitatory", "inhibitory"]

    @overrides(AbstractNeuronImpl.get_recordable_variables)
    def get_recordable_variables(self) -> Sequence[str]:
        return ["v", "ex_input", "in_input", "prob"]

    @overrides(AbstractNeuronImpl.get_recordable_data_types)
    def get_recordable_data_types(self) -> Mapping[str, DataType]:
        return {"v": DataType.S1615,
                "ex_input": DataType.S1615, "in_input": DataType.S1615,
                "prob": DataType.U032}

    @overrides(AbstractNeuronImpl.get_recordable_units)
    def get_recordable_units(self, variable: str) -> Optional[str]:
        # TODO: Update with the appropriate units for variables
        if variable in ("v", "ex_input", "in_input"):
            return "mV"
        elif variable == "prob":
            return ""
        raise ValueError("Unknown variable {}".format(variable))

    @overrides(AbstractNeuronImpl.get_recordable_variable_index)
    def get_recordable_variable_index(self, variable: str) -> Optional[int]:
        if variable == "v":
            return 0
        if variable == "ex_input":
            return 1
        if variable == "in_input":
            return 2
        if variable == "prob":
            return 3
        raise ValueError("Unknown variable {}".format(variable))

    @overrides(AbstractNeuronImpl.is_recordable)
    def is_recordable(self, variable: str) -> bool:
        # TODO: Update to identify variables that can be recorded
        return variable in ("v", "ex_input", "in_input", "prob")

    @overrides(AbstractNeuronImpl.add_parameters)
    def add_parameters(self, parameters: RangeDictionary):
        parameters[TAU] = self._tau
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()
        parameters[BIAS] = self._bias

    @overrides(AbstractNeuronImpl.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary):
        state_variables[REFRACT_INIT] = self._refract_init
        state_variables[SEED0] = self._random
        state_variables[SEED1] = self._random
        state_variables[SEED2] = self._random
        state_variables[SEED3] = self._random

    @overrides(AbstractNeuronImpl.get_units)
    def get_units(self, variable: str) -> str:
        return UNITS[variable]

    @property
    @overrides(AbstractNeuronImpl.is_conductance_based)
    def is_conductance_based(self) -> bool:
        return False

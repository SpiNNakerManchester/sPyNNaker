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

from spinn_front_end_common.interface.ds import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractNeuronImpl)
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from pyNN.random import NumpyRNG

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

    def __init__(self, tau, bias, refract_init, seed):

        self._tau = tau
        self._bias = bias
        self._refract_init = refract_init
        self._seed = seed

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
    def structs(self):
        return [self._struct]

    @property
    @overrides(AbstractNeuronImpl.model_name)
    def model_name(self):
        return "StocExp"

    @property
    @overrides(AbstractNeuronImpl.binary_name)
    def binary_name(self):
        return "stoc_exp.aplx"

    @overrides(AbstractNeuronImpl.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1.0

    @overrides(AbstractNeuronImpl.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 2

    @overrides(AbstractNeuronImpl.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        raise ValueError("Unknown target {}".format(target))

    @overrides(AbstractNeuronImpl.get_synapse_targets)
    def get_synapse_targets(self):
        return ["excitatory", "inhibitory"]

    @overrides(AbstractNeuronImpl.get_recordable_variables)
    def get_recordable_variables(self):
        return ["v", "ex_input", "in_input"]

    @overrides(AbstractNeuronImpl.get_recordable_data_types)
    def get_recordable_data_types(self):
        return {"v": DataType.S1615,
                "ex_input": DataType.S1615, "in_input": DataType.S1615}

    @overrides(AbstractNeuronImpl.get_recordable_units)
    def get_recordable_units(self, variable):
        # TODO: Update with the appropriate units for variables
        if variable in ("v", "ex_input", "in_input"):
            return "mV"
        raise ValueError("Unknown variable {}".format(variable))

    @overrides(AbstractNeuronImpl.get_recordable_variable_index)
    def get_recordable_variable_index(self, variable):
        # TODO: Update with the index in the recorded_variable_values array
        # that the given variable will be recorded in to
        if variable != "v":
            raise ValueError("Unknown variable {}".format(variable))
        return 0

    @overrides(AbstractNeuronImpl.is_recordable)
    def is_recordable(self, variable):
        # TODO: Update to identify variables that can be recorded
        return variable in ("v", "ex_input", "in_input")

    @overrides(AbstractNeuronImpl.add_parameters)
    def add_parameters(self, parameters):
        parameters[TAU] = self._tau
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()
        parameters[BIAS] = self._bias

    @overrides(AbstractNeuronImpl.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[REFRACT_INIT] = self._refract_init
        rng = NumpyRNG(self._seed)
        state_variables[SEED0] = int(rng.next() * MAX_INT)
        state_variables[SEED1] = int(rng.next() * MAX_INT)
        state_variables[SEED2] = int(rng.next() * MAX_INT)
        state_variables[SEED3] = int(rng.next() * MAX_INT)

    @overrides(AbstractNeuronImpl.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @property
    @overrides(AbstractNeuronImpl.is_conductance_based)
    def is_conductance_based(self):
        return False

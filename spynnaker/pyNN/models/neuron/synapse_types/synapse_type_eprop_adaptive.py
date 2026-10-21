# Copyright (c) 2019 The University of Manchester
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
from spinn_utilities.ranged.range_dictionary import RangeDictionary

from spinn_front_end_common.interface.ds import DataType

from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.utilities.struct import Struct

from .abstract_synapse_type import AbstractSynapseType

ISYN_EXC = "isyn_exc"
ISYN_EXC2 = "isyn_exc2"
ISYN_INH = "isyn_inh"
ISYN_INH2 = "isyn_inh2"


class SynapseTypeEPropAdaptive(AbstractSynapseType):
    """ A synapse type that implements the e-prop learning rule with
        adaptive currents.
    """
    __slots__ = [
        "_isyn_exc",
        "_isyn_exc2",
        "_isyn_inh",
        "_isyn_inh2"]

    def __init__(
            self, isyn_exc: ModelParameter, isyn_exc2: ModelParameter,
            isyn_inh: ModelParameter, isyn_inh2: ModelParameter) -> None:
        """
        :param isyn_exc: The excitatory synaptic current
        :param isyn_exc2: The second excitatory synaptic current
        :param isyn_inh: The inhibitory synaptic current
        :param isyn_inh2: The second inhibitory synaptic current
        """
        super().__init__(
            [Struct([
                (DataType.S1615, ISYN_EXC),
                (DataType.S1615, ISYN_EXC2),
                (DataType.S1615, ISYN_INH),
                (DataType.S1615, ISYN_INH2)])],
            {ISYN_EXC: "", ISYN_EXC2: "",
             ISYN_INH: "", ISYN_INH2: ""})

        self._isyn_exc = isyn_exc
        self._isyn_exc2 = isyn_exc2
        self._isyn_inh = isyn_inh
        self._isyn_inh2 = isyn_inh2

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        pass

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        state_variables[ISYN_EXC] = self._convert(self._isyn_exc)
        state_variables[ISYN_EXC2] = self._convert(self._isyn_exc2)
        state_variables[ISYN_INH] = self._convert(self._isyn_inh)
        state_variables[ISYN_INH2] = self._convert(self._isyn_inh2)

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        return 4

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> int | None:
        if target == "input_connections":
            return 0
        elif target == "recurrent_connections":
            return 1
        elif target == "learning_signal":
            return 2
        elif target == "unused":
            return 3
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self) -> list[str]:
        return ["input_connections", "recurrent_connections",
                "learning_signal", "unused"]

    @property
    def isyn_exc(self) -> ModelParameter:
        """ The excitatory synaptic current """
        return self._isyn_exc

    @isyn_exc.setter
    def isyn_exc(self, isyn_exc: ModelParameter) -> None:
        """ Set the excitatory synaptic current """
        self._isyn_exc = isyn_exc

    @property
    def isyn_inh(self) -> ModelParameter:
        """ The inhibitory synaptic current """
        return self._isyn_inh

    @isyn_inh.setter
    def isyn_inh(self, isyn_inh: ModelParameter) -> None:
        """ Set the inhibitory synaptic current """
        self._isyn_inh = isyn_inh

    @property
    def isyn_inh2(self) -> ModelParameter:
        """ The second inhibitory synaptic current """
        return self._isyn_inh2

    @isyn_inh2.setter
    def isyn_inh2(self, isyn_inh2: ModelParameter) -> None:
        """ Set the second inhibitory synaptic current """
        self._isyn_inh2 = isyn_inh2

    @property
    def isyn_exc2(self) -> ModelParameter:
        """ The second excitatory synaptic current """
        return self._isyn_exc2

    @isyn_exc2.setter
    def isyn_exc2(self, isyn_exc2: ModelParameter) -> None:
        """ Set the second excitatory synaptic current """
        self._isyn_exc2 = isyn_exc2

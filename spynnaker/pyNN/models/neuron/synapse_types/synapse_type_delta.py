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

from typing import Optional, Tuple

from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary
from spinn_front_end_common.interface.ds import DataType

from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.utilities.struct import Struct

from .abstract_synapse_type import AbstractSynapseType

ISYN_EXC = "isyn_exc"
ISYN_INH = "isyn_inh"


class SynapseTypeDelta(AbstractSynapseType):
    """
    This represents a synapse type with two delta synapses.
    """
    __slots__ = (
        "__isyn_exc",
        "__isyn_inh")

    def __init__(self, isyn_exc: ModelParameter, isyn_inh: ModelParameter):
        """
        :param isyn_exc: :math:`I^{syn}_e`
        :param isyn_inh: :math:`I^{syn}_i`
        """
        super().__init__(
            [Struct([
                (DataType.S1615, ISYN_EXC),  # isyn_exc
                (DataType.S1615, ISYN_INH)])],  # isyn_inh
            {ISYN_EXC: "", ISYN_EXC: ""})
        self.__isyn_exc = isyn_exc
        self.__isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        pass

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        state_variables[ISYN_EXC] = self._convert(self.__isyn_exc)
        state_variables[ISYN_INH] = self._convert(self.__isyn_inh)

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        return 2

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self) -> Tuple[str, ...]:
        return "excitatory", "inhibitory"

    @property
    def isyn_exc(self) -> ModelParameter:
        """
        Value as passed into the init.
        """
        return self.__isyn_exc

    @property
    def isyn_inh(self) -> ModelParameter:
        """
        Value as passed into the init.
        """
        return self.__isyn_inh

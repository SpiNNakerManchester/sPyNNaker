# Copyright (c) 2015 The University of Manchester
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
from spynnaker.pyNN.data import SpynnakerDataView

from .abstract_synapse_type import AbstractSynapseType

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_I = 'tau_syn_I'
ISYN_EXC = "isyn_exc"
ISYN_INH = "isyn_inh"
TIMESTEP_MS = "timestep_ms"


class SynapseTypeExponential(AbstractSynapseType):
    """
    A simple exponential synapse.
    """
    __slots__ = (
        "__tau_syn_E",
        "__tau_syn_I",
        "__isyn_exc",
        "__isyn_inh")

    def __init__(self, tau_syn_E: ModelParameter, tau_syn_I: ModelParameter,
                 isyn_exc: ModelParameter, isyn_inh: ModelParameter):
        r"""
        :param tau_syn_E: :math:`\tau^{syn}_e`
        :type tau_syn_E: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_syn_I: :math:`\tau^{syn}_i`
        :type tau_syn_I: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param isyn_exc: :math:`I^{syn}_e`
        :type isyn_exc: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param isyn_inh: :math:`I^{syn}_i`
        :type isyn_inh: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, TAU_SYN_E),
                (DataType.S1615, ISYN_EXC),
                (DataType.S1615, TAU_SYN_I),
                (DataType.S1615, ISYN_INH),
                (DataType.S1615, TIMESTEP_MS)])],
            {TAU_SYN_E: "mV", TAU_SYN_I: 'mV', ISYN_EXC: "", ISYN_INH: ""})
        # pylint: disable=invalid-name
        self.__tau_syn_E = tau_syn_E
        self.__tau_syn_I = tau_syn_I
        self.__isyn_exc = isyn_exc
        self.__isyn_inh = isyn_inh

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]):
        parameters[TAU_SYN_E] = self._convert(self.__tau_syn_E)
        parameters[TAU_SYN_I] = self._convert(self.__tau_syn_I)
        parameters[TIMESTEP_MS] = (
            SpynnakerDataView.get_simulation_time_step_ms())

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary[float]):
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
    def tau_syn_E(self) -> ModelParameter:
        # pylint: disable=invalid-name
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__tau_syn_E

    @property
    def tau_syn_I(self) -> ModelParameter:
        # pylint: disable=invalid-name
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__tau_syn_I

    @property
    def isyn_exc(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__isyn_exc

    @property
    def isyn_inh(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__isyn_inh

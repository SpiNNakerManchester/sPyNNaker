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
from .abstract_synapse_type import AbstractSynapseType
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

EXC_RESPONSE = "exc_response"
EXC_EXP_RESPONSE = "exc_exp_response"
TAU_SYN_E = "tau_syn_E"
INH_RESPONSE = "inh_response"
INH_EXP_RESPONSE = "inh_exp_response"
TAU_SYN_I = "tau_syn_I"
Q_EXC = "q_exc"
Q_INH = "q_inh"
TIMESTEP_MS = "timestep_ms"


class SynapseTypeAlpha(AbstractSynapseType):
    """
    Alpha Type Synapse
    """
    __slots__ = (
        "__exc_exp_response",
        "__exc_response",
        "__inh_exp_response",
        "__inh_response",
        "__tau_syn_E",
        "__tau_syn_I",
        "__q_exc",
        "__q_inh")

    def __init__(
            self, exc_response: ModelParameter,
            exc_exp_response: ModelParameter, tau_syn_E: ModelParameter,
            inh_response: ModelParameter, inh_exp_response: ModelParameter,
            tau_syn_I: ModelParameter):
        r"""
        :param exc_response: :math:`response^\mathrm{linear}_e`
        :type exc_response: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param exc_exp_response: :math:`response^\mathrm{exponential}_e`
        :type exc_exp_response: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_syn_E: :math:`\tau^{syn}_e`
        :type tau_syn_E: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param inh_response: :math:`response^\mathrm{linear}_i`
        :type inh_response: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param inh_exp_response: :math:`response^\mathrm{exponential}_i`
        :type inh_exp_response: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_syn_I: :math:`\tau^{syn}_i`
        :type tau_syn_I: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, EXC_RESPONSE),
                (DataType.S1615, EXC_EXP_RESPONSE),
                (DataType.S1615, Q_EXC),
                (DataType.S1615, TAU_SYN_E),
                (DataType.S1615, INH_RESPONSE),
                (DataType.S1615, INH_EXP_RESPONSE),
                (DataType.S1615, Q_INH),
                (DataType.S1615, TAU_SYN_I),
                (DataType.S1615, TIMESTEP_MS)])],
            {EXC_RESPONSE: "", EXC_EXP_RESPONSE: "", TAU_SYN_E: "ms",
             INH_RESPONSE: "", INH_EXP_RESPONSE: "", TAU_SYN_I: "ms"})

        # pylint: disable=too-many-arguments
        self.__exc_response = exc_response
        self.__exc_exp_response = exc_exp_response
        # pylint: disable=invalid-name
        self.__tau_syn_E = tau_syn_E
        self.__inh_response = inh_response
        self.__inh_exp_response = inh_exp_response
        self.__tau_syn_I = tau_syn_I

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]):
        parameters[TAU_SYN_E] = self._convert(self.__tau_syn_E)
        parameters[TAU_SYN_I] = self._convert(self.__tau_syn_I)

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary[float]):
        state_variables[EXC_RESPONSE] = self._convert(self.__exc_response)
        state_variables[EXC_EXP_RESPONSE] = self._convert(
            self.__exc_exp_response)
        state_variables[Q_EXC] = 0
        state_variables[INH_RESPONSE] = self._convert(self.__inh_response)
        state_variables[INH_EXP_RESPONSE] = self._convert(
            self.__inh_exp_response)
        state_variables[Q_INH] = 0
        state_variables[TIMESTEP_MS] = (
            SpynnakerDataView.get_simulation_time_step_ms())

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        return 2  # excitatory and inhibitory

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
    def exc_response(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__exc_response

    @exc_response.setter
    def exc_response(self, exc_response: ModelParameter):
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        self.__exc_response = exc_response

    @property
    def tau_syn_E(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        # pylint: disable=invalid-name
        return self.__tau_syn_E

    @property
    def inh_response(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__inh_response

    @property
    def tau_syn_I(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        # pylint: disable=invalid-name
        return self.__tau_syn_I

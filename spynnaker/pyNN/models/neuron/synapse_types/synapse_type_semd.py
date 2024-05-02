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
from spynnaker.pyNN.data import SpynnakerDataView

from .abstract_synapse_type import AbstractSynapseType

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_E2 = 'tau_syn_E2'
TAU_SYN_I = 'tau_syn_I'
ISYN_EXC = "isyn_exc"
ISYN_EXC2 = "isyn_exc2"
ISYN_INH = "isyn_inh"
MULTIPLICATOR = "multiplicator"
EXC2_OLD = "exc2_old"
SCALING_FACTOR = "scaling_factor"
TIMESTEP_MS = "timestep_ms"


class SynapseTypeSEMD(AbstractSynapseType):
    """
    Synapse for a Leaky integrate and fire neuron with an exponentially
    decaying current input, where the excitatory input depends upon the
    inhibitory input (see https://www.cit-ec.de/en/nbs/spiking-insect-vision)
    """
    __slots__ = (
        "__tau_syn_E",
        "__tau_syn_E2",
        "__tau_syn_I",
        "__isyn_exc",
        "__isyn_exc2",
        "__isyn_inh",
        "__multiplicator",
        "__exc2_old",
        "__scaling_factor")

    def __init__(
            self, tau_syn_E: ModelParameter, tau_syn_E2: ModelParameter,
            tau_syn_I: ModelParameter, isyn_exc: ModelParameter,
            isyn_exc2: ModelParameter, isyn_inh: ModelParameter,
            multiplicator: ModelParameter, exc2_old: ModelParameter,
            scaling_factor: ModelParameter):
        r"""
        :param tau_syn_E: :math:`\tau^{syn}_{e_1}`
        :type tau_syn_E: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_syn_E2: :math:`\tau^{syn}_{e_2}`
        :type tau_syn_E2: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_syn_I: :math:`\tau^{syn}_i`
        :type tau_syn_I: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param isyn_exc: :math:`I^{syn}_{e_1}`
        :type isyn_exc: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param isyn_exc2: :math:`I^{syn}_{e_2}`
        :type isyn_exc2: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param isyn_inh: :math:`I^{syn}_i`
        :type isyn_inh: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param multiplicator:
        :type multiplicator: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param exc2_old:
        :type exc2_old: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param scaling_factor:
        :type scaling_factor: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, TAU_SYN_E),
                (DataType.S1615, ISYN_EXC),
                (DataType.S1615, TAU_SYN_E2),
                (DataType.S1615, ISYN_EXC2),
                (DataType.S1615, TAU_SYN_I),
                (DataType.S1615, ISYN_INH),
                (DataType.S1615, MULTIPLICATOR),
                (DataType.S1615, EXC2_OLD),
                (DataType.S1615, SCALING_FACTOR),
                (DataType.S1615, TIMESTEP_MS)])],
            {TAU_SYN_E: "mV", TAU_SYN_E2: "mV", TAU_SYN_I: 'mV', ISYN_EXC: "",
             ISYN_EXC2: "", ISYN_INH: "", MULTIPLICATOR: "", EXC2_OLD: "",
             SCALING_FACTOR: ""})
        # pylint: disable=invalid-name
        self.__tau_syn_E = tau_syn_E
        self.__tau_syn_E2 = tau_syn_E2
        self.__tau_syn_I = tau_syn_I
        self.__isyn_exc = isyn_exc
        self.__isyn_exc2 = isyn_exc2
        self.__isyn_inh = isyn_inh
        self.__multiplicator = multiplicator
        self.__exc2_old = exc2_old
        self.__scaling_factor = scaling_factor

    @overrides(AbstractSynapseType.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]):
        parameters[TAU_SYN_E] = self._convert(self.__tau_syn_E)
        parameters[TAU_SYN_E2] = self._convert(self.__tau_syn_E2)
        parameters[TAU_SYN_I] = self._convert(self.__tau_syn_I)
        parameters[TIMESTEP_MS] = (
            SpynnakerDataView.get_simulation_time_step_ms())
        parameters[SCALING_FACTOR] = self._convert(self.__scaling_factor)

    @overrides(AbstractSynapseType.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary[float]):
        state_variables[ISYN_EXC] = self._convert(self.__isyn_exc)
        state_variables[ISYN_EXC2] = self._convert(self.__isyn_exc2)
        state_variables[ISYN_INH] = self._convert(self.__isyn_inh)
        state_variables[EXC2_OLD] = self._convert(self.__exc2_old)
        state_variables[MULTIPLICATOR] = self._convert(self.__multiplicator)

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self) -> int:
        return 3

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target: str) -> Optional[int]:
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self) -> Tuple[str, ...]:
        return "excitatory", "excitatory2", "inhibitory"

    @property
    def tau_syn_E(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        # pylint: disable=invalid-name
        return self.__tau_syn_E

    @property
    def tau_syn_E2(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        # pylint: disable=invalid-name
        return self.__tau_syn_E2

    @property
    def tau_syn_I(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        # pylint: disable=invalid-name
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

    @property
    def isyn_exc2(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__isyn_exc2

    @property
    def multiplicator(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__multiplicator

    @property
    def exc2_old(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__exc2_old

    @property
    def scaling_factor(self) -> ModelParameter:
        """
        Value as passed into the init.

        :rtype: ModelParameter
        """
        return self.__scaling_factor

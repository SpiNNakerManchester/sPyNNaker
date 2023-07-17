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

from typing import Optional
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary
from spinn_front_end_common.interface.ds import DataType
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent, ModelParameter)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView
from .neuron_model import NeuronModel

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
TIMESTEP = "timestep"
REFRACT_TIMER = "refract_timer"


class NeuronModelLeakyIntegrateAndFire(NeuronModel):
    """
    Classic leaky integrate and fire neuron model.
    """
    __slots__ = (
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac")

    def __init__(
            self, v_init: Optional[ModelParameter], v_rest: ModelParameter,
            tau_m: ModelParameter, cm: ModelParameter,
            i_offset: ModelParameter, v_reset: ModelParameter,
            tau_refrac: ModelParameter):
        r"""
        :param v_init: :math:`V_{init}`
        :type v_init: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param v_rest: :math:`V_{rest}`
        :type v_rest: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_m: :math:`\tau_{m}`
        :type tau_m: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param cm: :math:`C_m`
        :type cm: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param i_offset: :math:`I_{offset}`
        :type i_offset: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param v_reset: :math:`V_{reset}`
        :type v_reset: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        :param tau_refrac: :math:`\tau_{refrac}`
        :type tau_refrac: float or iterable(float) or
            ~spynnaker.pyNN.RandomDistribution or (mapping) function
        """
        super().__init__(
            [Struct([
                (DataType.S1615, V),
                (DataType.S1615, V_REST),
                (DataType.S1615, CM),
                (DataType.S1615, TAU_M),
                (DataType.S1615, I_OFFSET),
                (DataType.S1615, V_RESET),
                (DataType.S1615, TAU_REFRAC),
                (DataType.INT32, REFRACT_TIMER),
                (DataType.S1615, TIMESTEP)])],
            {V: 'mV', V_REST: 'mV', TAU_M: 'ms', CM: 'nF', I_OFFSET: 'nA',
             V_RESET: 'mV', TAU_REFRAC: 'ms'})

        if v_init is None:
            v_init = v_rest
        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]):
        parameters[V_REST] = self._convert(self.__v_rest)
        parameters[TAU_M] = self._convert(self.__tau_m)
        parameters[CM] = self._convert(self.__cm)
        parameters[I_OFFSET] = self._convert(self.__i_offset)
        parameters[V_RESET] = self._convert(self.__v_reset)
        parameters[TAU_REFRAC] = self._convert(self.__tau_refrac)
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables: RangeDictionary[float]):
        state_variables[V] = self._convert(self.__v_init)
        state_variables[REFRACT_TIMER] = 0

    @property
    def v_init(self) -> ModelParameter:
        """
        Settable model parameter: :math:`V_{init}`

        :rtype: float
        """
        return self.__v_init

    @property
    def v_rest(self) -> ModelParameter:
        """
        Settable model parameter: :math:`V_{rest}`

        :rtype: float
        """
        return self.__v_rest

    @property
    def tau_m(self) -> ModelParameter:
        r"""
        Settable model parameter: :math:`\tau_{m}`

        :rtype: float
        """
        return self.__tau_m

    @property
    def cm(self) -> ModelParameter:
        """
        Settable model parameter: :math:`C_m`

        :rtype: float
        """
        return self.__cm

    @property
    def i_offset(self) -> ModelParameter:
        """
        Settable model parameter: :math:`I_{offset}`

        :rtype: float
        """
        return self.__i_offset

    @property
    def v_reset(self) -> ModelParameter:
        """
        Settable model parameter: :math:`V_{reset}`

        :rtype: float
        """
        return self.__v_reset

    @property
    def tau_refrac(self) -> ModelParameter:
        r"""
        Settable model parameter: :math:`\tau_{refrac}`

        :rtype: float
        """
        return self.__tau_refrac

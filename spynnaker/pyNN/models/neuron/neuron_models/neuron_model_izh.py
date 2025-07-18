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
from spinn_utilities.overrides import overrides
from spinn_utilities.ranged import RangeDictionary
from spinn_front_end_common.interface.ds import DataType
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent, ModelParameter)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView
from .neuron_model import NeuronModel

A = 'a'
B = 'b'
C = 'c'
D = 'd'
V = 'v'
U = 'u'
I_OFFSET = 'i_offset'
TIMESTEP = 'timestep'
NEXT_H = 'next_h'


class NeuronModelIzh(NeuronModel):
    """
    Model of neuron due to Eugene M. Izhikevich et al.
    """
    __slots__ = (
        "__a", "__b", "__c", "__d",
        "__v_init", "__u_init", "__i_offset")

    def __init__(
            self, a: ModelParameter, b: ModelParameter, c: ModelParameter,
            d: ModelParameter, v_init: ModelParameter, u_init: ModelParameter,
            i_offset: ModelParameter):
        """
        :param a: :math:`a`
        :param b: :math:`b`
        :param c: :math:`c`
        :param d: :math:`d`
        :param v_init: :math:`v_{init}`
        :param u_init: :math:`u_{init}`
        :param i_offset: :math:`I_{offset}`
        """
        super().__init__(
            [Struct([
                (DataType.S1615, A),
                (DataType.S1615, B),
                (DataType.S1615, C),
                (DataType.S1615, D),
                (DataType.S1615, V),
                (DataType.S1615, U),
                (DataType.S1615, I_OFFSET),
                (DataType.S1615, TIMESTEP),
                (DataType.S1615, NEXT_H)])],
            {A: "ms", B: "ms", C: "mV", D: "mV/ms", V: "mV", U: "mV/ms",
             I_OFFSET: "nA"})
        self.__a = a
        self.__b = b
        self.__c = c
        self.__d = d
        self.__i_offset = i_offset
        self.__v_init = v_init
        self.__u_init = u_init

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters: RangeDictionary[float]) -> None:
        parameters[A] = self._convert(self.__a)
        parameters[B] = self._convert(self.__b)
        parameters[C] = self._convert(self.__c)
        parameters[D] = self._convert(self.__d)
        parameters[I_OFFSET] = self._convert(self.__i_offset)
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(
            self, state_variables: RangeDictionary[float]) -> None:
        state_variables[V] = self._convert(self.__v_init)
        state_variables[U] = self._convert(self.__u_init)
        state_variables[NEXT_H] = (
            SpynnakerDataView.get_simulation_time_step_ms())

    @property
    def a(self) -> ModelParameter:
        """
        Settable model parameter: :math:`a`
        """
        return self.__a

    @property
    def b(self) -> ModelParameter:
        """
        Settable model parameter: :math:`b`
        """
        return self.__b

    @property
    def c(self) -> ModelParameter:
        """
        Settable model parameter: :math:`c`
        """
        return self.__c

    @property
    def d(self) -> ModelParameter:
        """
        Settable model parameter: :math:`d`
        """
        return self.__d

    @property
    def i_offset(self) -> ModelParameter:
        """
        Settable model parameter: :math:`I_{offset}`
        """
        return self.__i_offset

    @property
    def v_init(self) -> ModelParameter:
        """
        Settable model parameter: :math:`v_{init}`
        """
        return self.__v_init

    @property
    def u_init(self) -> ModelParameter:
        """
        Settable model parameter: :math:`u_{init}`
        """
        return self.__u_init

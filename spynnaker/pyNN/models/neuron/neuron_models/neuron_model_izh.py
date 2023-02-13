# Copyright (c) 2015-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

A = 'a'
B = 'b'
C = 'c'
D = 'd'
V = 'v'
U = 'u'
I_OFFSET = 'i_offset'
TIMESTEP = 'timestep'
NEXT_H = 'next_h'


class NeuronModelIzh(AbstractStandardNeuronComponent):
    """ Model of neuron due to Eugene M. Izhikevich et al
    """
    __slots__ = [
        "__a", "__b", "__c", "__d", "__v_init", "__u_init", "__i_offset"
    ]

    def __init__(self, a, b, c, d, v_init, u_init, i_offset):
        """
        :param a: :math:`a`
        :type a: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param b: :math:`b`
        :type b: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param c: :math:`c`
        :type c: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param d: :math:`d`
        :type d: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param v_init: :math:`v_{init}`
        :type v_init:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param u_init: :math:`u_{init}`
        :type u_init:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param i_offset: :math:`I_{offset}`
        :type i_offset:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
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
    def add_parameters(self, parameters):
        parameters[A] = self.__a
        parameters[B] = self.__b
        parameters[C] = self.__c
        parameters[D] = self.__d
        parameters[I_OFFSET] = self.__i_offset
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[U] = self.__u_init
        state_variables[NEXT_H] = (
            SpynnakerDataView.get_simulation_time_step_ms())

    @property
    def a(self):
        """ Settable model parameter: :math:`a`

        :rtype: float
        """
        return self.__a

    @property
    def b(self):
        """ Settable model parameter: :math:`b`

        :rtype: float
        """
        return self.__b

    @property
    def c(self):
        """ Settable model parameter: :math:`c`

        :rtype: float
        """
        return self.__c

    @property
    def d(self):
        """ Settable model parameter: :math:`d`

        :rtype: float
        """
        return self.__d

    @property
    def i_offset(self):
        """ Settable model parameter: :math:`I_{offset}`

        :rtype: float
        """
        return self.__i_offset

    @property
    def v_init(self):
        """ Settable model parameter: :math:`v_{init}`

        :rtype: float
        """
        return self.__v_init

    @property
    def u_init(self):
        """ Settable model parameter: :math:`u_{init}`

        :rtype: float
        """
        return self.__u_init

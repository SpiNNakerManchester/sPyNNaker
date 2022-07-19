# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_MILLISECOND_CONVERSION)
from .abstract_neuron_model import AbstractNeuronModel
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)

A = 'a'
B = 'b'
C = 'c'
D = 'd'
V = 'v'
U = 'u'
I_OFFSET = 'i_offset'

UNITS = {
    A: "ms",
    B: "ms",
    C: "mV",
    D: "mV/ms",
    V: "mV",
    U: "mV/ms",
    I_OFFSET: "nA"
}


class NeuronModelIzh(AbstractNeuronModel):
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
            [DataType.S1615,   # a
             DataType.S1615,   # b
             DataType.S1615,   # c
             DataType.S1615,   # d
             DataType.S1615,   # v
             DataType.S1615,   # u
             DataType.S1615,   # i_offset
             DataType.S1615],  # this_h (= machine_time_step)
            [DataType.S1615])  # machine_time_step
        self.__a = a
        self.__b = b
        self.__c = c
        self.__d = d
        self.__i_offset = i_offset
        self.__v_init = v_init
        self.__u_init = u_init

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        parameters[A] = self.__a
        parameters[B] = self.__b
        parameters[C] = self.__c
        parameters[D] = self.__d
        parameters[I_OFFSET] = self.__i_offset

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[U] = self.__u_init

    @overrides(AbstractStandardNeuronComponent.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractStandardNeuronComponent.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractNeuronModel.get_global_values)
    def get_global_values(self, ts):
        return [float(ts) / MICRO_TO_MILLISECOND_CONVERSION]

    @overrides(AbstractStandardNeuronComponent.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """
        :param ts: machine time step
        """
        # Add the rest of the data
        return [
            parameters[A], parameters[B], parameters[C], parameters[D],
            state_variables[V], state_variables[U], parameters[I_OFFSET],
            float(ts) / MICRO_TO_MILLISECOND_CONVERSION
        ]

    @overrides(AbstractStandardNeuronComponent.update_values)
    def update_values(self, values, parameters, state_variables):

        # Decode the values
        _a, _b, _c, _d, v, u, _i_offset, _this_h = values

        # Copy the changed data only
        state_variables[V] = v
        state_variables[U] = u

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

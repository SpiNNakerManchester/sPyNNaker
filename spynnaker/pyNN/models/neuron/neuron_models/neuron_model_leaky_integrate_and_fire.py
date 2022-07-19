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

import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_neuron_model import AbstractNeuronModel
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
COUNT_REFRAC = "count_refrac"

UNITS = {
    V: 'mV',
    V_REST: 'mV',
    TAU_M: 'ms',
    CM: 'nF',
    I_OFFSET: 'nA',
    V_RESET: 'mV',
    TAU_REFRAC: 'ms'
}


class NeuronModelLeakyIntegrateAndFire(AbstractNeuronModel):
    """ Classic leaky integrate and fire neuron model.
    """
    __slots__ = [
        "__v_init",
        "__v_rest",
        "__tau_m",
        "__cm",
        "__i_offset",
        "__v_reset",
        "__tau_refrac"]

    def __init__(
            self, v_init, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac):
        r"""
        :param v_init: :math:`V_{init}`
        :type v_init:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param v_rest: :math:`V_{rest}`
        :type v_rest:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param tau_m: :math:`\tau_{m}`
        :type tau_m:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param cm: :math:`C_m`
        :type cm: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param i_offset: :math:`I_{offset}`
        :type i_offset:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param v_reset: :math:`V_{reset}`
        :type v_reset:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param tau_refrac: :math:`\tau_{refrac}`
        :type tau_refrac:
            float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        """
        super().__init__(
            [DataType.S1615,   # v
             DataType.S1615,   # v_rest
             DataType.S1615,   # r_membrane (= tau_m / cm)
             DataType.U032,   # exp_tc (= e^(-ts / tau_m))
             DataType.S1615,   # i_offset
             DataType.INT32,   # count_refrac
             DataType.S1615,   # v_reset
             DataType.INT32])  # tau_refrac

        if v_init is None:
            v_init = v_rest
        self.__v_init = v_init
        self.__v_rest = v_rest
        self.__tau_m = tau_m
        self.__cm = cm
        self.__i_offset = i_offset
        self.__v_reset = v_reset
        self.__tau_refrac = tau_refrac

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 100 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[COUNT_REFRAC] = 0

    @overrides(AbstractStandardNeuronComponent.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractStandardNeuronComponent.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractStandardNeuronComponent.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """
        :param int ts: machine time step
        """
        # Add the rest of the data
        return [state_variables[V], parameters[V_REST],
                parameters[TAU_M] / parameters[CM],
                parameters[TAU_M].apply_operation(
                    operation=lambda x: numpy.exp(float(-ts) / (1000.0 * x))),
                parameters[I_OFFSET], state_variables[COUNT_REFRAC],
                parameters[V_RESET],
                parameters[TAU_REFRAC].apply_operation(
                    operation=lambda x: int(numpy.ceil(x / (ts / 1000.0))))]

    @overrides(AbstractStandardNeuronComponent.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (v, _v_rest, _r_membrane, _exp_tc, _i_offset, count_refrac,
         _v_reset, _tau_refrac) = values

        # Copy the changed data only
        state_variables[V] = v
        state_variables[COUNT_REFRAC] = count_refrac

    @property
    def v_init(self):
        """ Settable model parameter: :math:`V_{init}`

        :rtype: float
        """
        return self.__v_init

    @property
    def v_rest(self):
        """ Settable model parameter: :math:`V_{rest}`

        :rtype: float
        """
        return self.__v_rest

    @property
    def tau_m(self):
        r""" Settable model parameter: :math:`\tau_{m}`

        :rtype: float
        """
        return self.__tau_m

    @property
    def cm(self):
        """ Settable model parameter: :math:`C_m`

        :rtype: float
        """
        return self.__cm

    @property
    def i_offset(self):
        """ Settable model parameter: :math:`I_{offset}`

        :rtype: float
        """
        return self.__i_offset

    @property
    def v_reset(self):
        """ Settable model parameter: :math:`V_{reset}`

        :rtype: float
        """
        return self.__v_reset

    @property
    def tau_refrac(self):
        r""" Settable model parameter: :math:`\tau_{refrac}`

        :rtype: float
        """
        return self.__tau_refrac

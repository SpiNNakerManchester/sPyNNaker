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
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)
from spynnaker.pyNN.utilities.struct import Struct
from spynnaker.pyNN.data import SpynnakerDataView

V = "v"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
V_RESET = "v_reset"
TAU_REFRAC = "tau_refrac"
TIMESTEP = "timestep"
REFRACT_TIMER = "refract_timer"


class NeuronModelLeakyIntegrateAndFire(AbstractStandardNeuronComponent):
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
    def add_parameters(self, parameters):
        parameters[V_REST] = self.__v_rest
        parameters[TAU_M] = self.__tau_m
        parameters[CM] = self.__cm
        parameters[I_OFFSET] = self.__i_offset
        parameters[V_RESET] = self.__v_reset
        parameters[TAU_REFRAC] = self.__tau_refrac
        parameters[TIMESTEP] = SpynnakerDataView.get_simulation_time_step_ms()

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[V] = self.__v_init
        state_variables[REFRACT_TIMER] = 0

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

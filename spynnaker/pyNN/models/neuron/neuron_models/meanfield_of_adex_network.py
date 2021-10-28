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

###--Meanfield Params--###
NBR = "nbr"
A = "a"
B = "b"
TAUW = "tauw"
TREFRAC = "Trefrac"
VRESET = "Vreset"
DELTA_V = "delta_v"
AMPNOISE = "ampnoise"
TIMESCALE_INV = "Timescale_inv"
VE = "Ve"
VI = "Vi"

UNITS = {
    ###--Meanfield--###
    NBR: "",
    A: "nS",
    B: "nS",
    TAUW: "ms",
    TREFRAC: "ms",
    VRESET: "mV",
    DELTA_V: "mV",
    AMPNOISE: "Hz",
    TIMESCALE_INV: "Hz",
    VE: "Hz",
    VI: "Hz",
}


class MeanfieldOfAdexNetwork(AbstractNeuronModel):
    """ Model of meanfield due to A.Destehexe et al
    """
    __slots__ = [
        "_nbr", "_a", "_b", "_tauw", "_Trefrac", "_Vreset", "_delta_v",
        "_ampnoise", "_Timescale_inv", "_Ve_init", "_Vi_init"
    ]

    def __init__(self, nbr, a, b, tauw,
                 Trefrac, Vreset, delta_v,
                 ampnoise, Timescale_inv, Ve_init, Vi_init):
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
            [DataType.UINT32, #nbr
            DataType.S1615, #a
            DataType.S1615, #b
            DataType.S1615, #tauw
            DataType.S1615, #Trefrac
            DataType.S1615, #Vreset
            DataType.S1615, #delta_v
            DataType.S1615, #ampnoise
            DataType.S1615, #Timescale_inv
            DataType.S1615, #Ve
            DataType.S1615, #Vi            
            DataType.S1615],  # this_h (= machine_time_step)
            [DataType.S1615])  # machine_time_step
        self._nbr = nbr
        self._a = a
        self._b = b
        self._tauw = tauw
        self._Trefrac = Trefrac
        self._Vreset =Vreset
        self._delta_v = delta_v
        self._ampnoise = ampnoise
        self._Timescale_inv = Timescale_inv
        self._Ve_init = Ve_init
        self._Vi_init = Vi_init

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        ###--neuron--###
        parameters[NBR] = self._nbr
        parameters[A] = self._a
        parameters[B] = self._b
        parameters[TAUW] = self._tauw
        parameters[TREFRAC] = self._Trefrac
        parameters[VRESET] = self._Vreset
        parameters[DELTA_V] = self._delta_v
        parameters[AMPNOISE] = self._ampnoise
        parameters[TIMESCALE_INV] = self._Timescale_inv

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[VE] = self._Ve_init
        state_variables[VI] = self._Vi_init

    @overrides(AbstractStandardNeuronComponent.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractStandardNeuronComponent.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractNeuronModel.get_global_values)
    def get_global_values(self, ts):
        # pylint: disable=arguments-differ
        return [float(ts) / MICRO_TO_MILLISECOND_CONVERSION]

    @overrides(AbstractStandardNeuronComponent.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """
        :param ts: machine time step
        """
        # pylint: disable=arguments-differ

        # Add the rest of the data
        return [
            parameters[NBR],parameters[A],parameters[B],parameters[TAUW],
            parameters[TREFRAC],
            parameters[VRESET],parameters[DELTA_V],parameters[AMPNOISE],
            parameters[TIMESCALE_INV],
            state_variables[VE],
            state_variables[VI],
            float(ts) / MICRO_TO_MILLISECOND_CONVERSION
        ]

    @overrides(AbstractStandardNeuronComponent.update_values)
    def update_values(self, values, parameters, state_variables):

        # Decode the values
        (_nbr, _a, _b, _tauw,
        _Trefrac, _Vreset, _delta_v,
        _ampnoise, _Timescale_inv, Ve, Vi, _this_h) = values

        # Copy the changed data only
        state_variables[VE] = Ve
        state_variables[VI] = Vi
        #state_variables[U] = u

################
###--Meanfield--###
################

    @property
    def nbr(self):
        return self._nbr


    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    @property
    def tauw(self):
        return self._tauw

    @property
    def Trefrac(self):
        return self._Trefrac

    @property
    def Vreset(self):
        return self._Vreset

    @property
    def delta_v(self):
        return self._delta_v

    @property
    def ampnoise(self):
        return self._ampnoise

    @property
    def Timescale_inv(self):
        return self._Timescale_inv

    @property
    def Ve_init(self):
        """ Settable model parameter: :math:`V_{e}`

        :rtype: float
        """
        return self._Ve_init

    @property
    def Vi_init(self):
        """ Settable model parameter: :math:`V_{i}`

        :rtype: float
        """
        return self._Vi_init    


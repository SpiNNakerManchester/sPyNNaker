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
from .abstract_input_type import AbstractInputType
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)

###--transfert function inputs from 'data_test/'+NRN1+'_'+NTWK+'_fit.npy' --###
P0 = "p0_exc"
P1 = "p1_exc"
P2 = "p2_exc"
P3 = "p3_exc"
P4 = "p4_exc"
P5 = "p5_exc"
P6 = "p6_exc"
P7 = "p7_exc"
P8 = "p8_exc"
P9 = "p9_exc"
P10 = "p10_exc"

UNITS = {
    P0 : "",
    P1 : "",
    P2 : "",
    P3 : "",
    P4 : "",
    P5 : "",
    P6 : "",
    P7 : "",
    P8 : "",
    P9 : "",
    P10 : "",
}


class pFitPolynomialExc(AbstractInputType):
    """ Model of neuron due to ...
    """
    __slots__ = [
        "__p0_exc", "__p1_exc", "__p2_exc", "__p3_exc", "__p4_exc", "__p5_exc",
        "__p6_exc", "__p7_exc", "__p8_exc", "__p9_exc", "__p10_exc"
    ]

    def __init__(self,
                 p0_exc, p1_exc, p2_exc, p3_exc, p4_exc, p5_exc,
                 p6_exc, p7_exc, p8_exc, p9_exc, p10_exc):
        """
        :param a: :math:`a`
        :type a: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        
        """
        super().__init__(
            
            [###--TF inputs--###
             DataType.S031, #p0
             DataType.S031, #p1
             DataType.S031, #p2
             DataType.S031, #p3
             DataType.S031, #p4
             DataType.S031, #p5
             DataType.S031, #p6
             DataType.S031, #p7
             DataType.S031, #p8
             DataType.S031, #p9
             DataType.S031]) #p10
        
        self.__p0_exc = p0_exc
        self.__p1_exc = p1_exc
        self.__p2_exc = p2_exc
        self.__p3_exc = p3_exc
        self.__p4_exc = p4_exc
        self.__p5_exc = p5_exc
        self.__p6_exc = p6_exc
        self.__p7_exc = p7_exc
        self.__p8_exc = p8_exc
        self.__p9_exc = p9_exc
        self.__p10_exc = p10_exc        

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        ###--TF inputs--###
        parameters[P0] = self.__p0_exc
        parameters[P1] = self.__p1_exc
        parameters[P2] = self.__p2_exc
        parameters[P3] = self.__p3_exc
        parameters[P4] = self.__p4_exc
        parameters[P5] = self.__p5_exc
        parameters[P6] = self.__p6_exc
        parameters[P7] = self.__p7_exc
        parameters[P8] = self.__p8_exc
        parameters[P9] = self.__p9_exc
        parameters[P10] = self.__p10_exc

    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        pass
    @overrides(AbstractStandardNeuronComponent.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractStandardNeuronComponent.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractNeuronModel.get_global_values)
    def get_global_values(self, ts):
        # pylint: disable=arguments-differ
        pass

    @overrides(AbstractStandardNeuronComponent.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        """
        :param ts: machine time step
        """
        # pylint: disable=arguments-differ

        # Add the rest of the data
        return [parameters[P0],#TF input
                parameters[P1],
                parameters[P2],
                parameters[P3],
                parameters[P4],
                parameters[P5],
                parameters[P6],
                parameters[P7],
                parameters[P8],
                parameters[P9],
                parameters[P10]
        ]

    @overrides(AbstractStandardNeuronComponent.update_values)
    def update_values(self, values, parameters, state_variables):

        # Decode the values
        (__p0_exc, __p1_exc, __p2_exc, __p3_exc, __p4_exc,
        __p5_exc, __p6_exc, __p7_exc, __p8_exc, __p9_exc, __p10_exc) = values
        
    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

###################
###--TF inputs--###
###################

    @property
    def p0_exc(self):
        return self.__p0_exc
        
    @property
    def p1_exc(self):
        return self._p1_exc

    @property
    def p2_exc(self):
        return self._p2_exc

    @property
    def p3_exc(self):
        return self._p3_exc

    @property
    def p4_exc(self):
        return self._p4_exc

    @property
    def p5_exc(self):
        return self._p5_exc
        
    @property
    def p6_exc(self):
        return self._p6_exc

    @property
    def p6_exc(self):
        return self._p6_exc

    @property
    def p7_exc(self):
        return self._p7_exc

    @property
    def p8_exc(self):
        return self._p8_exc

    @property
    def p9_exc(self):
        return self._p9_exc

    @property
    def p10_exc(self):
        return self._p10_exc

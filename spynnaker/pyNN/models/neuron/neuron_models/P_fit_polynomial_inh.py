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
P0 = "p0_inh"
P1 = "p1_inh"
P2 = "p2_inh"
P3 = "p3_inh"
P4 = "p4_inh"
P5 = "p5_inh"
P6 = "p6_inh"
P7 = "p7_inh"
P8 = "p8_inh"
P9 = "p9_inh"
P10 = "p10_inh"

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


class pFitPolynomialInh(AbstractInputType):
    """ Model of neuron due to ...
    """
    __slots__ = [
        "__p0_inh", "__p1_inh", "__p2_inh", "__p3_inh", "__p4_inh", "__p5_inh",
        "__p6_inh", "__p7_inh", "__p8_inh", "__p9_inh", "__p10_inh"
    ]

    def __init__(self,
                 p0_inh, p1_inh, p2_inh, p3_inh, p4_inh, p5_inh,
                 p6_inh, p7_inh, p8_inh, p9_inh, p10_inh):
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
        
        self.__p0_inh = p0_inh
        self.__p1_inh = p1_inh
        self.__p2_inh = p2_inh
        self.__p3_inh = p3_inh
        self.__p4_inh = p4_inh
        self.__p5_inh = p5_inh
        self.__p6_inh = p6_inh
        self.__p7_inh = p7_inh
        self.__p8_inh = p8_inh
        self.__p9_inh = p9_inh
        self.__p10_inh = p10_inh        

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        ###--TF inputs--###
        parameters[P0] = self.__p0_inh
        parameters[P1] = self.__p1_inh
        parameters[P2] = self.__p2_inh
        parameters[P3] = self.__p3_inh
        parameters[P4] = self.__p4_inh
        parameters[P5] = self.__p5_inh
        parameters[P6] = self.__p6_inh
        parameters[P7] = self.__p7_inh
        parameters[P8] = self.__p8_inh
        parameters[P9] = self.__p9_inh
        parameters[P10] = self.__p10_inh

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
        (__p0_inh, __p1_inh, __p2_inh, __p3_inh, __p4_inh,
        __p5_inh, __p6_inh, __p7_inh, __p8_inh, __p9_inh, __p10_inh) = values
        
    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

###################
###--TF inputs--###
###################

    @property
    def p0_inh(self):
        return self.__p0_inh
        
    @property
    def p1_inh(self):
        return self._p1_inh

    @property
    def p2_inh(self):
        return self._p2_inh

    @property
    def p3_inh(self):
        return self._p3_inh

    @property
    def p4_inh(self):
        return self._p4_inh

    @property
    def p5_inh(self):
        return self._p5_inh
        
    @property
    def p6_inh(self):
        return self._p6_inh

    @property
    def p6_inh(self):
        return self._p6_inh

    @property
    def p7_inh(self):
        return self._p7_inh

    @property
    def p8_inh(self):
        return self._p8_inh

    @property
    def p9_inh(self):
        return self._p9_inh

    @property
    def p10_inh(self):
        return self._p10_inh

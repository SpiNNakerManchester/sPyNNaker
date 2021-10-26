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
P0 = "p0"
P1 = "p1"
P2 = "p2"
P3 = "p3"
P4 = "p4"
P5 = "p5"
P6 = "p6"
P7 = "p7"
P8 = "p8"
P9 = "p9"
P10 = "p10"

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


class pFitPolynomial(AbstractInputType):
    """ Model of neuron due to Eugene M. Izhikevich et al
    """
    __slots__ = [
        "_p0", "_p1", "_p2", "_p3", "_p4", "_p5",
        "_p6", "_p7", "_p8", "_p9", "_p10"
    ]

    def __init__(self,
                 p0, p1, p2, p3, p4, p5,
                 p6, p7, p8, p9, p10,):
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
        
        self._p0 = p0
        self._p1 = p1
        self._p2 = p2
        self._p3 = p3
        self._p4 = p4
        self._p5 = p5
        self._p6 = p6
        self._p7 = p7
        self._p8 = p8
        self._p9 = p9
        self._p10 = p10        

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        ###--TF inputs--###
        parameters[P0] = self._p0
        parameters[P1] = self._p1
        parameters[P2] = self._p2
        parameters[P3] = self._p3
        parameters[P4] = self._p4
        parameters[P5] = self._p5
        parameters[P6] = self._p6
        parameters[P7] = self._p7
        parameters[P8] = self._p8
        parameters[P9] = self._p9
        parameters[P10] = self._p10

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
        (_p0, _p1, _p2, _p3, _p4,
        _p5, _p6, _p7, _p8, _p9, _p10) = values
        
    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

###################
###--TF inputs--###
###################

    @property
    def p0(self):
        return self._p0
        
    @property
    def p1(self):
        return self._p1

    @property
    def p2(self):
        return self._p2

    @property
    def p3(self):
        return self._p3

    @property
    def p4(self):
        return self._p4

    @property
    def p5(self):
        return self._p5
        
    @property
    def p6(self):
        return self._p6

    @property
    def p6(self):
        return self._p6

    @property
    def p7(self):
        return self._p7

    @property
    def p8(self):
        return self._p8

    @property
    def p9(self):
        return self._p9

    @property
    def p10(self):
        return self._p10

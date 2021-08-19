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

###--Meanfield Params--###
SAMPLE = "sample"
ERR_FUNC = "err_func"

UNITS = {
    ###--Meanfield--###
    SAMPLE: "",
    ERR_FUNC: "",
}


class Mathsbox(AbstractInputType):
    """ Model of meanfield due to Destehexe et al
    """
    __slots__ = ["_sample", "_err_func"]

    def __init__(self, sample, err_func):
        """
        :param a: :math:`a`
        :type a: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        :param b: :math:`b`
        :type b: float, iterable(float), ~pyNN.random.RandomDistribution or
            (mapping) function
        
        """
        super().__init__(
            [DataType.UINT32, #sample
            DataType.S1615]) # error fonction
        self._sample = sample
        self._err_func = err_func

    @overrides(AbstractStandardNeuronComponent.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 150 * n_neurons

    @overrides(AbstractStandardNeuronComponent.add_parameters)
    def add_parameters(self, parameters):
        ###--neuron--###
        parameters[SAMPLE] = self._sample
        
    @overrides(AbstractStandardNeuronComponent.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[ERR_FUNC] = self._err_func

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
        return [
            parameters[SAMPLE], state_variables[ERR_FUNC],
        ]

    @overrides(AbstractStandardNeuronComponent.update_values)
    def update_values(self, values, parameters, state_variables):

        # Decode the values
        _sample = values

        # Copy the changed data only
        state_variables[ERR_FUNC] = err_func
        #state_variables[U] = u

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0
    
################
###--Meanfield--###
################

    @property
    def sample(self):
        return self._sample

    
    @property
    def err_func(self):
        return self._err_func

    
        
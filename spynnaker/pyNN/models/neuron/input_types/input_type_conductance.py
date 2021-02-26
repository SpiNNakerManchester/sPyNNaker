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
from .abstract_input_type import AbstractInputType

E_REV_E = "e_rev_E"
E_REV_I = "e_rev_I"

UNITS = {
    E_REV_E: "mV",
    E_REV_I: "mV"
}


class InputTypeConductance(AbstractInputType):
    """ The conductance input type
    """
    __slots__ = [
        "__e_rev_E",
        "__e_rev_I"]

    def __init__(self, e_rev_E, e_rev_I):
        """
        :param e_rev_E: Reversal potential for excitatory input;
            :math:`E^{rev}_e`
        :type e_rev_E:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param e_rev_I: Reversal potential for inhibitory input;
            :math:`E^{rev}_i`
        :type e_rev_I:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__([
            DataType.S1615,   # e_rev_E
            DataType.S1615])  # e_rev_I
        self.__e_rev_E = e_rev_E
        self.__e_rev_I = e_rev_I

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 10 * n_neurons

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        parameters[E_REV_E] = self.__e_rev_E
        parameters[E_REV_I] = self.__e_rev_I

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [parameters[E_REV_E], parameters[E_REV_I]]

    @overrides(AbstractInputType.update_values)
    def update_values(self, values, parameters, state_variables):
        pass

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

    @property
    def e_rev_E(self):
        """
        :math:`E_{{rev}_e}`
        """
        return self.__e_rev_E

    @property
    def e_rev_I(self):
        """
        :math:`E_{{rev}_i}`
        """
        return self.__e_rev_I

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

MULTIPLICATOR = "multiplicator"
INH_INPUT_PREVIOUS = "inh_input_previous"

UNITS = {
    MULTIPLICATOR: "0",
    INH_INPUT_PREVIOUS: "mV"
}


class InputTypeCurrentSEMD(AbstractInputType):
    """ The current sEMD input type.
    """
    __slots__ = [
        "__multiplicator",
        "__inh_input_previous"]

    def __init__(self, multiplicator, inh_input_previous):
        """
        :param multiplicator:
        :type multiplicator:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        :param inh_input_previous:
        :type inh_input_previous:
            float, iterable(float), ~pyNN.random.RandomDistribution
            or (mapping) function
        """
        super().__init__([
            DataType.S1615,   # multiplicator
            DataType.S1615])  # inh_input_previous
        self.__multiplicator = multiplicator
        self.__inh_input_previous = inh_input_previous

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        parameters[MULTIPLICATOR] = self.__multiplicator

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[INH_INPUT_PREVIOUS] = self.__inh_input_previous

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        # Add the rest of the data
        return [parameters[MULTIPLICATOR], state_variables[INH_INPUT_PREVIOUS]]

    @overrides(AbstractInputType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_multiplicator, inh_input_previous) = values

        state_variables[INH_INPUT_PREVIOUS] = inh_input_previous

    @property
    def multiplicator(self):
        return self.__multiplicator

    @property
    def inh_input_previous(self):
        return self.__inh_input_previous

    def get_global_weight_scale(self):
        return 1.0

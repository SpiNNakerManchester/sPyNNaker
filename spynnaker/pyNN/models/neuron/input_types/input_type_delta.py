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


class InputTypeDelta(AbstractInputType):
    """ The delta input type
    """
    __slots__ = []

    def __init__(self):
        """
        """
        super().__init__([
            DataType.S1615])  # scale_factor, calculated from timestep

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 1 * n_neurons

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        pass

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice, ts):
        # pylint: disable=arguments-differ
        scale_factor = 1000.0 / float(ts)
        return [scale_factor]

    @overrides(AbstractInputType.update_values)
    def update_values(self, values, parameters, state_variables):
        pass

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        raise KeyError(variable)

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return False

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1.0

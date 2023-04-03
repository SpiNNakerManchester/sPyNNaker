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
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence


# TODO: this doesn't have Aplus and Aminus?
class WeightDependenceEpropReg(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    __slots__ = [
        "__w_max",
        "__w_min",
        "__reg_rate"]

    def __init__(self, w_min=0.0, w_max=1.0, reg_rate=0.0):
        super().__init__()
        self.__w_min = w_min
        self.__w_max = w_max
        self.__reg_rate = reg_rate

    @property
    def w_min(self):
        return self.__w_min

    @property
    def w_max(self):
        return self.__w_max

    @property
    def reg_rate(self):
        return self.__reg_rate

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        # pylint: disable=protected-access
        if not isinstance(weight_dependence, WeightDependenceEpropReg):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus))

    @property
    def vertex_executable_suffix(self):
        return "reg"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Eprop_reg weight dependence only supports single terms")

        return (5  # Number of 32-bit parameters
                * 4) * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales,
            n_weight_terms):
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Eprop_reg weight dependence only supports single terms")

        # Loop through each synapse type's weight scale
        for w in synapse_weight_scales:
            spec.write_value(
                data=self.__w_min * global_weight_scale,
                data_type=DataType.S1615)
            spec.write_value(
                data=self.__w_max * global_weight_scale,
                data_type=DataType.S1615)

            spec.write_value(
                data=self.A_plus * global_weight_scale,
                data_type=DataType.S1615)
            spec.write_value(
                data=self.A_minus * global_weight_scale,
                data_type=DataType.S1615)

            spec.write_value(self.__reg_rate, data_type=DataType.S1615)

    @property
    def weight_maximum(self):
        return self.__w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['w_min', 'w_max'] #, 'A_plus', 'A_minus']

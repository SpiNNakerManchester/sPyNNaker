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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence
# Four words per synapse type
_SPACE_PER_SYNAPSE_TYPE = 4 * BYTES_PER_WORD


class WeightDependenceMultiplicative(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    """ A multiplicative weight dependence STDP rule.
    """
    __slots__ = [
        "__w_max",
        "__w_min"]
    __PARAM_NAMES = ('w_min', 'w_max', 'A_plus', 'A_minus')

    def __init__(self, w_min=0.0, w_max=1.0):
        """
        :param float w_min: :math:`w^{min}`
        :param float w_max: :math:`w^{max}`
        """
        super().__init__()
        self.__w_min = w_min
        self.__w_max = w_max

    @property
    def w_min(self):
        """ :math:`w^{min}`

        :rtype: float
        """
        return self.__w_min

    @property
    def w_max(self):
        """ :math:`w^{max}`

        :rtype: float
        """
        return self.__w_max

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceMultiplicative):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus))

    @property
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """
        return "multiplicative"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Multiplicative weight dependence only supports single terms")

        return _SPACE_PER_SYNAPSE_TYPE * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales,
            n_weight_terms):
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Multiplicative weight dependence only supports single terms")

        # Loop through each synapse type
        for _ in synapse_weight_scales:
            spec.write_value(data=self.__w_min * global_weight_scale,
                             data_type=DataType.S1615)
            spec.write_value(data=self.__w_max * global_weight_scale,
                             data_type=DataType.S1615)

            spec.write_value(data=self.A_plus, data_type=DataType.S1615)
            spec.write_value(data=self.A_minus, data_type=DataType.S1615)

    @property
    def weight_maximum(self):
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule

        :rtype: float
        """
        return self.__w_max

    @property
    def weight_minimum(self):
        """ The minimum weight that will ever be set in a synapse as a result\
            of this rule

        :rtype: float
        """
        return self.__w_min

    @overrides(AbstractWeightDependence.weight_change_minimum)
    def weight_change_minimum(self, min_delta):
        pot, dep = min_delta
        return min(pot * self.A_plus, dep * self.A_minus)

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return self.__PARAM_NAMES

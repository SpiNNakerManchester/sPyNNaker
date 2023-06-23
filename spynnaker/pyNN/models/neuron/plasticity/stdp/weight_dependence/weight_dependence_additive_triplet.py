# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence

# Six words per synapse type
_SPACE_PER_SYNAPSE_TYPE = 6 * BYTES_PER_WORD


class WeightDependenceAdditiveTriplet(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    """
    An triplet-based additive weight dependence STDP rule.
    """
    __slots__ = [
        "__a3_minus",
        "__a3_plus",
        "__w_max",
        "__w_min"]
    __PARAM_NAMES = ('w_min', 'w_max', 'A3_plus', 'A3_minus')

    default_parameters = {'w_min': 0.0, 'w_max': 1.0, 'A3_plus': 0.01,
                          'A3_minus': 0.01}

    # noinspection PyPep8Naming
    def __init__(
            self, w_min=default_parameters['w_min'],
            w_max=default_parameters['w_max'],
            A3_plus=default_parameters['A3_plus'],
            A3_minus=default_parameters['A3_minus']):
        """
        :param float w_min: :math:`w^{min}`
        :param float w_max: :math:`w^{max}`
        :param float A3_plus: :math:`A_3^+`
        :param float A3_minus: :math:`A_3^-`
        """
        super().__init__()
        self.__w_min = w_min
        self.__w_max = w_max
        self.__a3_plus = A3_plus
        self.__a3_minus = A3_minus

    @property
    def w_min(self):
        """
        :math:`w^{min}`

        :rtype: float
        """
        return self.__w_min

    @property
    def w_max(self):
        """
        :math:`w^{max}`

        :rtype: float
        """
        return self.__w_max

    @property
    def A3_plus(self):
        """
        :math:`A_3^+`

        :rtype: float
        """
        return self.__a3_plus

    @property
    def A3_minus(self):
        """
        :math:`A_3^-`

        :rtype: float
        """
        return self.__a3_minus

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence):
        if not isinstance(weight_dependence, WeightDependenceAdditiveTriplet):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus) and
            (self.__a3_plus == weight_dependence.A3_plus) and
            (self.__a3_minus == weight_dependence.A3_minus))

    @property
    def vertex_executable_suffix(self):
        """
        The suffix to be appended to the vertex executable for this rule.

        :rtype: str
        """
        return "additive"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        if n_weight_terms != 2:
            raise NotImplementedError(
                "Additive weight dependence only supports one or two terms")
        return _SPACE_PER_SYNAPSE_TYPE * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales,
            n_weight_terms):

        # Loop through each synapse type
        for _ in synapse_weight_scales:

            # Scale the weights
            spec.write_value(data=self.__w_min * global_weight_scale,
                             data_type=DataType.S1615)
            spec.write_value(data=self.__w_max * global_weight_scale,
                             data_type=DataType.S1615)

            # Based on http://data.andrewdavison.info/docs/PyNN/_modules/pyNN
            #                /standardmodels/synapses.html
            # Pre-multiply A+ and A- by Wmax
            spec.write_value(
                data=self.A_plus * self.__w_max * global_weight_scale,
                data_type=DataType.S1615)
            spec.write_value(
                data=self.A_minus * self.__w_max * global_weight_scale,
                data_type=DataType.S1615)
            spec.write_value(
                data=self.__a3_plus * self.__w_max * global_weight_scale,
                data_type=DataType.S1615)
            spec.write_value(
                data=self.__a3_minus * self.__w_max * global_weight_scale,
                data_type=DataType.S1615)

    @property
    @overrides(AbstractWeightDependence.weight_maximum)
    def weight_maximum(self):
        """
        The maximum weight that will ever be set in a synapse as a result
        of this rule.

        :rtype: float
        """
        return self.__w_max

    @property
    @overrides(AbstractWeightDependence.weight_minimum)
    def weight_minimum(self):
        return self.__w_min

    @overrides(AbstractWeightDependence.weight_change_minimum)
    def weight_change_minimum(self, min_delta):
        (a2_plus, a3_plus), (a2_minus, a3_minus) = min_delta
        min_pot = a2_plus * self.A_plus + a3_plus * self.__a3_plus
        min_dep = a2_minus * self.A_minus + a3_minus * self.__a3_minus
        return min(min_pot, min_dep)

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self):
        return self.__PARAM_NAMES

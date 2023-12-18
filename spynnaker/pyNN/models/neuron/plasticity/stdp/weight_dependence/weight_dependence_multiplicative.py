# Copyright (c) 2015 The University of Manchester
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
from typing import Iterable, List
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationGenerator)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence
# Four words per synapse type
_SPACE_PER_SYNAPSE_TYPE = 4 * BYTES_PER_WORD


class WeightDependenceMultiplicative(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    """
    A multiplicative weight dependence STDP rule.
    """
    __slots__ = (
        "__w_max",
        "__w_min")
    __PARAM_NAMES = ('w_min', 'w_max', 'A_plus', 'A_minus')

    def __init__(self, w_min: float = 0.0, w_max: float = 1.0):
        """
        :param float w_min: :math:`w^{min}`
        :param float w_max: :math:`w^{max}`
        """
        super().__init__()
        self.__w_min = w_min
        self.__w_max = w_max

    @property
    def w_min(self) -> float:
        """
        :math:`w^{min}`

        :rtype: float
        """
        return self.__w_min

    @property
    def w_max(self) -> float:
        """
        :math:`w^{max}`

        :rtype: float
        """
        return self.__w_max

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence: AbstractWeightDependence) -> bool:
        if not isinstance(weight_dependence, WeightDependenceMultiplicative):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus))

    @property
    def vertex_executable_suffix(self) -> str:
        """
        The suffix to be appended to the vertex executable for this rule.

        :rtype: str
        """
        return "multiplicative"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types: int, n_weight_terms: int) -> int:
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Multiplicative weight dependence only supports single terms")

        return _SPACE_PER_SYNAPSE_TYPE * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationGenerator, global_weight_scale: float,
            synapse_weight_scales: List[float], n_weight_terms: int):
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
    def weight_maximum(self) -> float:
        """
        The maximum weight that will ever be set in a synapse as a result
        of this rule.

        :rtype: float
        """
        return self.__w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        return self.__PARAM_NAMES

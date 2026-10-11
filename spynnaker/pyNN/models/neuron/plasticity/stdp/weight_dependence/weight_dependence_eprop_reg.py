# Copyright (c) 2019 The University of Manchester
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
from numpy import floating
from numpy.typing import NDArray

from spinn_utilities.overrides import overrides

from spinn_front_end_common.interface.ds import DataSpecificationBase, DataType

from .abstract_has_a_plus_a_minus import AbstractHasAPlusAMinus
from .abstract_weight_dependence import AbstractWeightDependence


class WeightDependenceEpropReg(
        AbstractHasAPlusAMinus, AbstractWeightDependence):
    """ Weight dependence for Eprop with regularization
    """

    __slots__ = [
        "__reg_rate",
        "__w_max",
        "__w_min"
    ]

    def __init__(
            self, w_min: float = 0.0, w_max: float = 1.0,
            reg_rate: float = 0.0):
        """
        :param w_min: The minimum weight
        :param w_max: The maximum weight
        :param reg_rate: The regularization rate
        """
        super().__init__()
        self.__w_min = w_min
        self.__w_max = w_max
        self.__reg_rate = reg_rate

    @property
    def w_min(self) -> float:
        """ The minimum weight """
        return self.__w_min

    @property
    def w_max(self) -> float:
        """ The maximum weight """
        return self.__w_max

    @property
    def reg_rate(self) -> float:
        """ The regularization rate """
        return self.__reg_rate

    @overrides(AbstractWeightDependence.is_same_as)
    def is_same_as(self, weight_dependence: AbstractWeightDependence) -> bool:
        # pylint: disable=protected-access
        if not isinstance(weight_dependence, WeightDependenceEpropReg):
            return False
        return (
            (self.__w_min == weight_dependence.w_min) and
            (self.__w_max == weight_dependence.w_max) and
            (self.A_plus == weight_dependence.A_plus) and
            (self.A_minus == weight_dependence.A_minus))

    @property
    @overrides(AbstractWeightDependence.vertex_executable_suffix)
    def vertex_executable_suffix(self) -> str:
        return "reg"

    @overrides(AbstractWeightDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types: int, n_weight_terms: int) -> int:
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Eprop_reg weight dependence only supports single terms")

        return (5  # Number of 32-bit parameters
                * 4) * n_synapse_types

    @overrides(AbstractWeightDependence.write_parameters)
    def write_parameters(
            self, spec: DataSpecificationBase, global_weight_scale: float,
            synapse_weight_scales: NDArray[floating],
            n_weight_terms: int) -> None:
        if n_weight_terms != 1:
            raise NotImplementedError(
                "Eprop_reg weight dependence only supports single terms")

        # Loop through each synapse type's weight scale
        for _ in synapse_weight_scales:
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
    def weight_maximum(self) -> float:
        """ The maximum weight """
        return self.__w_max

    @overrides(AbstractWeightDependence.get_parameter_names)
    def get_parameter_names(self) -> list[str]:
        return ['w_min', 'w_max']
